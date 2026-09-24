"""Decoupled Managed Agents Architecture (Apr 08, 2026).

Implements the tripartite decoupling:
1. The Brain: Stateless agent harness loop that reboots with wake(sessionId).
2. The Hands: Disposable 'cattle' sandboxes called via execute(name, input) -> str.
3. The Session: Append-only external durable event stream accessed via getEvents() and emitEvent().
4. Security Vault: OAuth tokens and Git auth isolated outside sandbox containers.
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SessionEvent:
    event_id: int
    timestamp: float
    event_type: str  # USER_MESSAGE, TOOL_CALL, TOOL_RESULT, AGENT_STEP, RECOVERY
    payload: Dict[str, Any]


class DurableSessionLog:
    """External durable event store that lives completely outside the context window."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: List[SessionEvent] = []
        self._next_id = 1

    def emit_event(self, event_type: str, payload: Dict[str, Any]) -> SessionEvent:
        evt = SessionEvent(
            event_id=self._next_id,
            timestamp=time.time(),
            event_type=event_type,
            payload=payload
        )
        self.events.append(evt)
        self._next_id += 1
        return evt

    def get_events(self, start_idx: int = 0, limit: Optional[int] = None) -> List[SessionEvent]:
        """Allows the brain to interrogate slices of the event history on demand."""
        sliced = self.events[start_idx:]
        if limit is not None:
            sliced = sliced[:limit]
        return sliced

    def get_summary_tokens(self) -> int:
        return len(self.events) * 45  # estimated


class CattleSandbox:
    """Disposable execution environment (the 'Hands'). Interchangeable and ephemeral."""

    def __init__(self, container_id: str, resources: Dict[str, Any], git_repo_url: str):
        self.container_id = container_id
        self.resources = resources
        self.git_repo_url = git_repo_url
        self.alive = True
        self.file_system: Dict[str, str] = {}
        # Notice: Access tokens are NOT stored in the filesystem or environment!

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Uniform execution interface: execute(name, input) -> string."""
        if not self.alive:
            raise RuntimeError(f"Cattle sandbox '{self.container_id}' is terminated or unresponsive.")

        if tool_name == "bash":
            cmd = arguments.get("command", "")
            # Simulate shell execution
            if "pkill" in cmd or "kill -9" in cmd:
                self.alive = False
                raise RuntimeError("Process signal terminated container environment.")
            return f"Executed `{cmd}` successfully. Output: [Exit code 0]"
        elif tool_name == "write_file":
            path = arguments.get("path", "")
            content = arguments.get("content", "")
            self.file_system[path] = content
            return f"Wrote {len(content)} bytes to {path}"
        elif tool_name == "read_file":
            path = arguments.get("path", "")
            return self.file_system.get(path, "File not found.")
        return f"Tool {tool_name} executed."

    def terminate(self):
        self.alive = False


class SecurityVault:
    """External credential manager; wires tokens into proxy requests, isolating sandboxes."""

    def __init__(self):
        self.git_tokens: Dict[str, str] = {}
        self.mcp_oauth_tokens: Dict[str, str] = {}

    def register_repo_token(self, repo_url: str, token: str):
        self.git_tokens[repo_url] = token

    def register_oauth_token(self, service: str, token: str):
        self.mcp_oauth_tokens[service] = token

    def proxy_git_clone_url(self, repo_url: str) -> str:
        """Injects authentication into the remote URL without exposing the token to the agent.

        Simulation: the vault records that a token exists for this repo, and a
        placeholder credential reaches the sandbox. In production a
        credential-helper socket outside the container injects the real token.
        """
        credential = (
            "x-access-token:[VAULT_ISOLATED]" if repo_url in self.git_tokens else "anonymous"
        )
        return f"https://{credential}@{repo_url.replace('https://', '')}"


class StatelessHarnessBrain:
    """The 'Brain': A stateless loop that directs Claude, easily rebooted on crash."""

    # Defaults used for self-healing re-provisioning in the reference simulation.
    DEFAULT_RESOURCES = {"cpu": 4, "mem": "8Gi"}
    DEFAULT_REPO_URL = "https://github.com/my-org/repo"

    def __init__(self, session_id: str, session_log: DurableSessionLog, vault: SecurityVault):
        self.session_id = session_id
        self.session_log = session_log
        self.vault = vault
        self.current_sandbox: Optional[CattleSandbox] = None
        self.current_event_idx = 0

    def wake(self):
        """Reboots harness from last event in durable session log with zero state loss."""
        events = self.session_log.get_events(start_idx=self.current_event_idx)
        self.current_event_idx += len(events)
        return len(events)

    def provision_sandbox_on_demand(self, resources: Dict[str, Any], repo_url: str) -> CattleSandbox:
        """Lazy provisioning drops TTFT by 60% p50 / 90% p95."""
        container_id = f"box_{uuid.uuid4().hex[:6]}"
        safe_repo_url = self.vault.proxy_git_clone_url(repo_url)
        self.current_sandbox = CattleSandbox(container_id, resources, safe_repo_url)
        for event in self.session_log.get_events():
            if event.event_type == "FILE_WRITTEN":
                path = event.payload["path"]
                self.current_sandbox.file_system[path] = event.payload["content"]
        self.session_log.emit_event("SANDBOX_PROVISIONED", {
            "container_id": container_id,
            "resources": resources
        })
        return self.current_sandbox

    def step(self, action_name: str, arguments: Dict[str, Any]) -> str:
        """Executes a step with automatic cattle failover recovery."""
        if not self.current_sandbox or not self.current_sandbox.alive:
            # Self-healing cattle provisioning
            self.provision_sandbox_on_demand(self.DEFAULT_RESOURCES, self.DEFAULT_REPO_URL)

        try:
            result = self.current_sandbox.execute(action_name, arguments)
            if action_name == "write_file":
                self.session_log.emit_event("FILE_WRITTEN", {
                    "path": arguments.get("path", ""),
                    "content": arguments.get("content", "")
                })
            self.session_log.emit_event("TOOL_RESULT", {"tool": action_name, "result": result})
            return result
        except RuntimeError as e:
            # Container died! Log tool error to session and re-provision
            self.session_log.emit_event("SANDBOX_CRASH", {"error": str(e)})
            # Re-provision fresh cattle sandbox immediately
            self.provision_sandbox_on_demand(self.DEFAULT_RESOURCES, self.DEFAULT_REPO_URL)
            retry_result = self.current_sandbox.execute(action_name, arguments)
            self.session_log.emit_event("TOOL_RECOVERY_SUCCESS", {"result": retry_result})
            return f"[CATTLE FAILOVER RECOVERED] Container crashed and auto-reprovisioned. Output: {retry_result}"
