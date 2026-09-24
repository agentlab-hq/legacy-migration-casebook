"""Claude Code Auto Mode Guardrails & Classifiers (Mar 25, 2026).

The *integrated* Auto Mode guardrail used by the demo stack. Since the
package consolidation this is a thin adapter over the canonical policy layer
in ``claude_auto_mode`` (injection probe, Tier 1 safe-tool allowlist, Tier 2
project boundary, Tier 3 policy engine, Deny-and-Continue budgets), so the
three-tier contract has exactly one implementation: probe patterns, tier
lists, sensitive paths, and block rules are all defined in ``claude_auto_mode``.

Public API (unchanged)::

    AutoModeGuardrail(project_root=...).evaluate_action(
        user_prompt, tool_name, arguments, tool_output
    ) -> AutoModeEvaluation
"""

import uuid
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from claude_auto_mode.injection_probe import PromptInjectionProbe  # re-exported for compatibility
from claude_auto_mode.pipeline import AutoModePipeline
from claude_auto_mode.types import ToolCall

from .types import AutoModeEvaluation, DecisionTier


class AutoModeGuardrail:
    """End-to-End Auto Mode Defense Pipeline (adapter over AutoModePipeline)."""

    def __init__(self, project_root: str = "/project"):
        self.project_root = Path(project_root).expanduser().resolve()
        self.pipeline = AutoModePipeline(project_root=str(self.project_root))
        # Preserve the compatibility attribute while sharing the canonical
        # probe instance used by the pipeline.
        self.probe = self.pipeline.probe

    @property
    def consecutive_denials(self) -> int:
        return self.pipeline.consecutive_denials

    @property
    def total_denials(self) -> int:
        return self.pipeline.total_denials

    def reset_budget(self) -> None:
        self.pipeline.reset_budget()

    def evaluate_action(
        self,
        user_prompt: str,
        tool_name: str,
        arguments: Optional[Mapping[str, Any]],
        tool_output: str = "",
    ) -> AutoModeEvaluation:
        """Evaluate a tool action and adapt the canonical decision DTO."""
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError("tool_name must be a non-empty string")
        if arguments is not None and not isinstance(arguments, Mapping):
            raise TypeError("arguments must be a mapping or None")

        args: Dict[str, Any] = dict(arguments or {})
        command = args.get("command", "")
        tool_call = ToolCall(
            id=f"call-{uuid.uuid4().hex[:8]}",
            tool_name=tool_name,
            arguments=args,
            executable_command="" if command is None else str(command),
        )
        decision = self.pipeline.evaluate(
            tool_call,
            user_prompt=user_prompt or "",
            tool_output=tool_output or "",
        )

        tier = decision.tier
        is_stage1 = tier == DecisionTier.TIER_3_STAGE_1
        is_stage2 = tier == DecisionTier.TIER_3_STAGE_2
        return AutoModeEvaluation(
            tier=tier,
            verdict=decision.verdict,
            stage1_verdict=decision.verdict if is_stage1 else None,
            stage2_reasoning=decision.reason if is_stage2 else None,
            # No classifier cache metric is produced by the deterministic
            # policy engine, so do not infer a cache hit from the tier.
            prompt_cache_hit=False,
            consecutive_denials=decision.consecutive_denials,
            total_denials=decision.total_denials,
            escalated_to_human=decision.escalated_to_human,
            reason=decision.reason,
            retry_guidance=decision.retry_feedback,
        )
