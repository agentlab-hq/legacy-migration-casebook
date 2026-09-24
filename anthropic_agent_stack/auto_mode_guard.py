"""Claude Code Auto Mode Guardrails & Classifiers (Mar 25, 2026).

The *integrated* Auto Mode guardrail used by the demo stack. Since the
package consolidation this is a thin adapter over the canonical policy layer
in ``claude_auto_mode`` (injection probe, Tier 1 safe-tool allowlist, Tier 2
project boundary, Tier 3 policy engine, Deny-and-Continue budgets), so the
three-tier contract has exactly one implementation: probe patterns, tier
lists, sensitive paths, and block rules are all defined in ``claude_auto_mode``.

Public API (unchanged):

    AutoModeGuardrail(project_root=...).evaluate_action(
        user_prompt, tool_name, arguments, tool_output
    ) -> AutoModeEvaluation
"""

import uuid
from pathlib import Path
from typing import Dict, Any

from claude_auto_mode.injection_probe import PromptInjectionProbe  # re-exported for compatibility
from claude_auto_mode.pipeline import AutoModePipeline
from claude_auto_mode.types import ToolCall

from .types import AutoModeEvaluation, DecisionTier, DecisionVerdict


class AutoModeGuardrail:
    """End-to-End Auto Mode Defense Pipeline (adapter over AutoModePipeline)."""

    def __init__(self, project_root: str = "/project"):
        self.project_root = Path(project_root).expanduser().resolve()
        self.pipeline = AutoModePipeline(project_root=str(self.project_root))
        self.probe = PromptInjectionProbe()

    # Backward-compatible budget views; authoritative state lives in the pipeline.
    @property
    def consecutive_denials(self) -> int:
        return self.pipeline.consecutive_denials

    @property
    def total_denials(self) -> int:
        return self.pipeline.total_denials

    def reset_budget(self):
        self.pipeline.reset_budget()

    def evaluate_action(
        self,
        user_prompt: str,
        tool_name: str,
        arguments: Dict[str, Any],
        tool_output: str = "",
    ) -> AutoModeEvaluation:
        args = dict(arguments or {})
        tool_call = ToolCall(
            id=f"call-{uuid.uuid4().hex[:8]}",
            tool_name=tool_name,
            arguments=args,
            executable_command=str(args.get("command", "")),
        )
        decision = self.pipeline.evaluate(tool_call, user_prompt=user_prompt, tool_output=tool_output)

        tier = decision.tier
        return AutoModeEvaluation(
            tier=tier,
            verdict=decision.verdict,
            stage1_verdict=(
                DecisionVerdict.BLOCK
                if tier == DecisionTier.TIER_3_STAGE_2
                else DecisionVerdict.ALLOW if tier == DecisionTier.TIER_3_STAGE_1
                else None
            ),
            stage2_reasoning=decision.reason if tier == DecisionTier.TIER_3_STAGE_2 else None,
            prompt_cache_hit=tier == DecisionTier.TIER_3_STAGE_2,
            consecutive_denials=decision.consecutive_denials,
            total_denials=decision.total_denials,
            escalated_to_human=decision.escalated_to_human,
            reason=decision.reason,
            retry_guidance=decision.retry_feedback,
        )
