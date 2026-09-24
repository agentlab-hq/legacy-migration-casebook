"""End-to-end Auto Mode pipeline — the canonical three-tier policy layer.

This is the single implementation of the Auto Mode defense-in-depth contract
used across the project. The integrated demo stack
(``anthropic_agent_stack.auto_mode_guard``) is a thin adapter over this
pipeline, so probe patterns, tier lists, sensitive paths, and block rules
exist in exactly one place.

Decision flow:

    Input-layer injection probe (demotes flagged tool output to passive data,
    anchored to the user directive)
        -> Tier 1 (safe-tool allowlist, blanket shell escapes stripped)
        -> Tier 2 (in-project file boundary; violations BLOCK here and never
           fall through to the command-rule classifier)
        -> Tier 3 (policy engine: 21 block rules with 3 allow exceptions)

Every block feeds the Deny-and-Continue retry budgets (3 consecutive /
20 total denials escalate to a human).
"""

from typing import List, Optional

from .injection_probe import PromptInjectionProbe
from .policy_engine import PolicyEngine, PolicyConfig
from .tier1_allowlist import Tier1Allowlist
from .tier2_project_boundary import Tier2ProjectBoundary
from .types import (
    AutoModeDecision,
    DecisionTier,
    DecisionVerdict,
    ToolCall,
    ToolResult,
)


class AutoModePipeline:
    """Three-tier decision pipeline with Deny-and-Continue retry budgets."""

    MAX_CONSECUTIVE_DENIALS = 3
    MAX_TOTAL_DENIALS = 20

    def __init__(
        self,
        project_root: str = "/project",
        config: Optional[PolicyConfig] = None,
        user_custom_allows: Optional[List[str]] = None,
    ):
        self.probe = PromptInjectionProbe()
        self.tier1 = Tier1Allowlist(user_custom_allows=user_custom_allows)
        self.tier2 = Tier2ProjectBoundary(project_root=project_root)
        self.policy = PolicyEngine(config)
        self.consecutive_denials = 0
        self.total_denials = 0

    def screen_tool_result(self, tool_result: ToolResult, tool_name: str = "tool", user_directive: str = "") -> ToolResult:
        """Input-layer defense: scan tool output before it reaches the model."""
        return self.probe.screen(tool_result, tool_name, user_directive)

    def evaluate(self, tool_call: ToolCall, user_prompt: str = "", tool_output: str = "") -> AutoModeDecision:
        """Evaluate one tool call.

        ``user_prompt`` is the authorization context shown to the (simulated)
        reasoning-blind classifier; ``tool_output`` is scanned by the
        input-layer probe first — a flagged output is treated as passive data
        and noted on the decision rather than changing the action verdict.
        """
        name = tool_call.tool_name.lower().strip()

        # Input-layer probe.
        probe_flagged = False
        if tool_output:
            probe_flagged = self.probe.scan_tool_result(name, tool_output, user_prompt)[0]

        # Tier 1: safe read-only tools clear immediately.
        allowed, reason = self.tier1.evaluate(tool_call)
        if allowed:
            decision = self._allow(DecisionTier.TIER_1_SAFE_ALLOWLIST, reason)
        else:
            # Tier 2: in-project file operations. File-edit tools that fail
            # the boundary (escape, sensitive file, missing path) are BLOCKED
            # here: falling through to command rules would silently allow them.
            allowed, reason = self.tier2.evaluate(tool_call)
            if allowed:
                decision = self._allow(DecisionTier.TIER_2_PROJECT_BOUNDARY, reason)
            elif name in self.tier2.FILE_EDIT_TOOLS:
                decision = self._block(
                    DecisionTier.TIER_2_PROJECT_BOUNDARY,
                    reason or "File operation failed Tier 2 boundary checks (missing or unsafe path).",
                    user_prompt,
                )
            else:
                # Tier 3: policy engine (block rules with allow exceptions).
                blocks, exception = self.policy.check_command(self._executable_command(tool_call))
                if not blocks:
                    if exception:
                        decision = self._allow(
                            DecisionTier.TIER_3_STAGE_1,
                            f"Cleared Tier 3: Matched allow exception {exception.id} ({exception.name}).",
                        )
                    else:
                        decision = self._allow(
                            DecisionTier.TIER_3_STAGE_1,
                            "Cleared Tier 3: No block rule matched the executable payload.",
                        )
                else:
                    decision = self._block(
                        DecisionTier.TIER_3_STAGE_2,
                        "; ".join(f"{b.id} {b.name}: {b.description}" for b in blocks),
                        user_prompt,
                    )

        if probe_flagged:
            decision.reason += (
                " Input-layer probe flagged the tool output; anchored to the user "
                "directive and treated as passive data."
            )
        return decision

    def _executable_command(self, tool_call: ToolCall) -> str:
        """Bare executable payload (reasoning-blind view input)."""
        if tool_call.executable_command:
            return tool_call.executable_command
        args = tool_call.arguments or {}
        return str(args.get("command", ""))

    def _allow(self, tier: DecisionTier, reason: str) -> AutoModeDecision:
        self.consecutive_denials = 0
        return AutoModeDecision(tier=tier, verdict=DecisionVerdict.ALLOW, reason=reason)

    def _block(self, tier: DecisionTier, reason: str, user_prompt: str = "") -> AutoModeDecision:
        self.consecutive_denials += 1
        self.total_denials += 1
        if user_prompt:
            reason = f"[user directive: {user_prompt!r}] " + reason
        return AutoModeDecision(
            tier=tier,
            verdict=DecisionVerdict.BLOCK,
            reason=reason,
            retry_feedback=(
                "ACTION BLOCKED: Find a safer alternative; do not attempt to bypass this boundary."
            ),
            consecutive_denials=self.consecutive_denials,
            total_denials=self.total_denials,
            escalated_to_human=(
                self.consecutive_denials >= self.MAX_CONSECUTIVE_DENIALS
                or self.total_denials >= self.MAX_TOTAL_DENIALS
            ),
        )

    def reset_budget(self):
        self.consecutive_denials = 0
        self.total_denials = 0
