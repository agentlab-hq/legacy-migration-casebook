"""End-to-end Auto Mode pipeline for the standalone policy layer.

Orchestrates the modules in this package as one decision pipeline:

    Input-layer injection probe -> Tier 1 (safe-tool allowlist)
        -> Tier 2 (in-project file boundary) -> Tier 3 (policy engine)

This mirrors the integrated guardrail in ``anthropic_agent_stack.auto_mode_guard``
so the two packages implement the same defense-in-depth contract: file edits
that fail the Tier 2 boundary are BLOCKED at that boundary (never silently
fall through to the command-rule classifier), and every block feeds the
Deny-and-Continue retry budgets.
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

    def screen_tool_result(self, tool_result: ToolResult, tool_name: str = "tool") -> ToolResult:
        """Input-layer defense: scan tool output before it reaches the model."""
        return self.probe.screen(tool_result, tool_name)

    def evaluate(self, tool_call: ToolCall) -> AutoModeDecision:
        name = tool_call.tool_name.lower().strip()

        # Tier 1: safe read-only tools clear immediately.
        allowed, reason = self.tier1.evaluate(tool_call)
        if allowed:
            self.consecutive_denials = 0
            return AutoModeDecision(
                tier=DecisionTier.TIER_1_SAFE_ALLOWLIST,
                verdict=DecisionVerdict.ALLOW,
                reason=reason,
            )

        # Tier 2: in-project file operations. File-edit tools that fail the
        # boundary (escape, sensitive file, or missing path) are BLOCKED here:
        # falling through to command rules would silently allow them.
        allowed, reason = self.tier2.evaluate(tool_call)
        if allowed:
            self.consecutive_denials = 0
            return AutoModeDecision(
                tier=DecisionTier.TIER_2_PROJECT_BOUNDARY,
                verdict=DecisionVerdict.ALLOW,
                reason=reason,
            )
        if name in self.tier2.FILE_EDIT_TOOLS:
            return self._block(
                DecisionTier.TIER_2_PROJECT_BOUNDARY,
                reason or "File operation failed Tier 2 boundary checks (missing or unsafe path).",
            )

        # Tier 3: policy engine (block rules with allow exceptions).
        blocks, exception = self.policy.check_command(self._executable_command(tool_call))
        if not blocks:
            self.consecutive_denials = 0
            if exception:
                return AutoModeDecision(
                    tier=DecisionTier.TIER_3_STAGE_1,
                    verdict=DecisionVerdict.ALLOW,
                    reason=f"Cleared Tier 3: Matched allow exception {exception.id} ({exception.name}).",
                )
            return AutoModeDecision(
                tier=DecisionTier.TIER_3_STAGE_1,
                verdict=DecisionVerdict.ALLOW,
                reason="Cleared Tier 3: No block rule matched the executable payload.",
            )
        return self._block(
            DecisionTier.TIER_3_STAGE_2,
            "; ".join(f"{b.id} {b.name}: {b.description}" for b in blocks),
        )

    def _executable_command(self, tool_call: ToolCall) -> str:
        """Bare executable payload (reasoning-blind view input)."""
        if tool_call.executable_command:
            return tool_call.executable_command
        args = tool_call.arguments or {}
        return str(args.get("command", ""))

    def _block(self, tier: DecisionTier, reason: str) -> AutoModeDecision:
        self.consecutive_denials += 1
        self.total_denials += 1
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
