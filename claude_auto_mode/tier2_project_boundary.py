"""Tier 2: In-Project File Operations Gate.

Allows routine file modifications inside the repository directory without paying
classifier latency, relying on local version control for auditability.
Sensitive system files or paths escaping the project root are rejected at Tier 2
and escalated to Tier 3.
"""

from pathlib import Path
from typing import Tuple, Optional, Set
from .types import ToolCall


class Tier2ProjectBoundary:
    """Verifies if file modifications are strictly confined within the project directory."""

    FILE_EDIT_TOOLS: Set[str] = {
        "write_file",
        "edit_file",
        "create_file",
        "append_file",
        "patch_file",
    }

    # Sensitive files within a repo that still require Tier 3 classifier review
    SENSITIVE_FILES: Set[str] = {
        ".git/config",
        ".git/credentials",
        ".env",
        ".env.local",
        ".env.production",
        ".bashrc",
        ".zshrc",
        ".ssh",
        "id_rsa",
        "id_ed25519",
        "authorized_keys",
        ".claude/permissions.json",
    }

    def __init__(self, project_root: str = "/home/user/workspace"):
        self.project_root = Path(project_root).resolve()

    def evaluate(self, tool_call: ToolCall) -> Tuple[bool, Optional[str]]:
        """Evaluates whether the file action is cleanly inside the project scope.
        
        Returns:
            Tuple of (is_allowed, reason)
        """
        name = tool_call.tool_name.lower().strip()
        if name not in self.FILE_EDIT_TOOLS:
            return False, None

        target_path_str = tool_call.arguments.get("path") or tool_call.arguments.get("file_path")
        if not target_path_str:
            return False, None

        # Resolve target path relative to project root
        try:
            target_path = Path(target_path_str)
            if not target_path.is_absolute():
                resolved_target = (self.project_root / target_path).resolve()
            else:
                resolved_target = target_path.resolve()
        except Exception:
            return False, None

        # Check path containment within project root
        try:
            rel = resolved_target.relative_to(self.project_root)
        except ValueError:
            return False, f"Target '{target_path_str}' escapes project directory '{self.project_root}'. Escalating to Tier 3."

        # Check for sensitive project files
        rel_str = str(rel).replace("\\", "/")
        for sensitive in self.SENSITIVE_FILES:
            if sensitive in rel_str or rel_str.endswith(sensitive):
                return False, f"Target file '{rel_str}' is security-sensitive. Escalating to Tier 3."

        return True, f"Cleared Tier 2: File edit on '{rel_str}' is within project root and auditable via git."
