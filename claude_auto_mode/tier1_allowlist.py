"""Tier 1: Safe-Tool Allowlist and User Settings Sanitizer.

Implements state-read-only tool filtering and actively strips blanket shell /
interpreter escapes configured from manual mode.
"""

from typing import Set, List, Tuple, Optional
from .types import ToolCall


class Tier1Allowlist:
    """Evaluates whether a tool call is inherently read-only / safe or covered by user rules."""

    # Inherently non-state-modifying tools that never require classifier evaluation
    SAFE_READ_TOOLS: Set[str] = {
        "read_file",
        "file_search",
        "grep_search",
        "code_navigation",
        "find_by_name",
        "list_directory",
        "view_outline",
        "todo_read",
        "plan_mode_transition",
        "git_status",
        "git_log",
        "git_diff_unstaged",
    }

    # Dangerous interpreter / shell commands that MUST NOT carry over blanket auto-approvals
    DANGEROUS_BLANKET_PATTERNS: List[str] = [
        "bash*",
        "sh*",
        "zsh*",
        "python*",
        "python3*",
        "node*",
        "npm run*",
        "npx*",
        "ruby*",
        "perl*",
        "eval*",
        "exec*",
        "sudo*",
        "docker run*",
    ]

    def __init__(self, user_custom_allows: Optional[List[str]] = None):
        """Initializes allowlist, sanitizing blanket permissions."""
        self.custom_allows = []
        if user_custom_allows:
            for rule in user_custom_allows:
                if self._is_blanket_execution_rule(rule):
                    # Silently or explicitly dropped on auto-mode entry
                    continue
                self.custom_allows.append(rule)

    def _is_blanket_execution_rule(self, rule_str: str) -> bool:
        """Checks if a user rule grants unrestricted arbitrary execution."""
        cleaned = rule_str.strip().lower()
        for blanket in self.DANGEROUS_BLANKET_PATTERNS:
            base = blanket.rstrip("*")
            if cleaned == base or cleaned.startswith(base) or cleaned == "*":
                return True
        return False

    def evaluate(self, tool_call: ToolCall) -> Tuple[bool, Optional[str]]:
        """Determines if the tool is cleared at Tier 1.
        
        Returns:
            Tuple of (is_allowed, reason)
        """
        name = tool_call.tool_name.lower().strip()
        
        # Check built-in safe read-only tools
        if name in self.SAFE_READ_TOOLS:
            return True, f"Cleared Tier 1: Built-in safe read-only tool '{name}' cannot modify persistent state."

        # Check narrow custom allowlist rules (e.g., formatters, linters)
        for rule in self.custom_allows:
            if rule.lower() in name or (tool_call.executable_command and rule.lower() in tool_call.executable_command.lower()):
                return True, f"Cleared Tier 1: Matched safe user-configured allow rule '{rule}'."

        return False, None
