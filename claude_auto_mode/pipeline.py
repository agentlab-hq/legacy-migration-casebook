"""End-to-end Auto Mode pipeline — the canonical three-tier policy layer."""

from typing import List, Optional

from .injection_probe import PromptInjectionProbe
from .policy_engine import PolicyEngine, PolicyConfig
from .tier1_allowlist import Tier1Allowlist
from .tier2_project_boundary import Tier2ProjectBoundary
from .types import AutoModeDecision, DecisionTier, DecisionVerdict, ToolCall, ToolResult


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

    def screen_tool_result(
        self,
        tool_result: ToolResult,
        tool_name: str = "tool",
        user_directive: str = "",
    ) -> ToolResult:
        """Input-layer defense: scan tool output before it reaches the model."""
        return self.probe.screen(tool_result, tool_name, user_directive)

    def evaluate(
        self,
        tool_call: ToolCall,
        user_prompt: str = "",
        tool_output: str = "",
    ) -> AutoModeDecision:
        """Evaluate one tool call through the probe and three policy tiers."""
        if not isinstance(tool_call, ToolCall):
            raise TypeError("tool_call must be a ToolCall")

        name = (tool_call.tool_name or "").lower().strip()
        probe_flagged = bool(tool_output) and self.probe.scan_tool_result(
            name, str(tool_output), user_prompt or ""
        )[0]

        allowed, reason = self.tier1.evaluate(tool_call)
        if allowed:
            decision = self._allow(DecisionTier.TIER_1_SAFE_ALLOWLIST, reason)
        else:
            allowed, reason = self.tier2.evaluate(tool_call)
            if allowed:
                decision = self._allow(DecisionTier.TIER_2_PROJECT_BOUNDARY, reason)
            elif name in self.tier2.FILE_EDIT_TOOLS:
                decision = self._block(
                    DecisionTier.TIER_2_PROJECT_BOUNDARY,
                    reason or "File operation failed Tier 2 boundary checks (missing or unsafe path).",
                    user_prompt or "",
                )
            else:
                blocks, exception = self.policy.check_command(self._executable_command(tool_call))
                if not blocks:
                    if exception:
                        reason = f"Cleared Tier 3: Matched allow exception {exception.id} ({exception.name})."
                    else:
                        reason = "Cleared Tier 3: No block rule matched the executable payload."
                    decision = self._allow(DecisionTier.TIER_3_STAGE_1, reason)
                else:
                    decision = self._block(
                        DecisionTier.TIER_3_STAGE_2,
                        "; ".join(f"{b.id} {b.name}: {b.description}" for b in blocks),
                        user_prompt or "",
                    )

        if probe_flagged:
            decision.reason += (
                " Input-layer probe flagged the tool output; anchored to the user "
                "directive and treated as passive data."
            )
        return decision

    def _executable_command(self, tool_call: ToolCall) -> str:
        if tool_call.executable_command:
            return str(tool_call.executable_command)
        command = (tool_call.arguments or {}).get("command", "")
        return "" if command is None else str(command)

    def _allow(self, tier: DecisionTier, reason: str) -> AutoModeDecision:
        self.consecutive_denials = 0
        # total_denials is a lifetime counter and must remain visible after an
        # allow; only consecutive_denials resets.
        return AutoModeDecision(
            tier=tier,
            verdict=DecisionVerdict.ALLOW,
            reason=reason,
            consecutive_denials=0,
            total_denials=self.total_denials,
        )

    def _block(self, tier: DecisionTier, reason: str, user_prompt: str = "") -> AutoModeDecision:
        self.consecutive_denials += 1
        self.total_denials += 1
        if user_prompt:
            reason = f"[user directive: {user_prompt!r}] " + reason
        return AutoModeDecision(
            tier=tier,
            verdict=DecisionVerdict.BLOCK,
            reason=reason,
            retry_feedback="ACTION BLOCKED: Find a safer alternative; do not attempt to bypass this boundary.",
            consecutive_denials=self.consecutive_denials,
            total_denials=self.total_denials,
            escalated_to_human=(
                self.consecutive_denials >= self.MAX_CONSECUTIVE_DENIALS
                or self.total_denials >= self.MAX_TOTAL_DENIALS
            ),
        )

    def reset_budget(self) -> None:
        self.consecutive_denials = 0
        self.total_denials = 0
