"""Append-only JSONL audit logging for policy decisions."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .types import AutoModeDecision, ToolCall


class JsonlAuditLogger:
    """Writes minimal, machine-readable policy decisions to an append-only log."""

    def __init__(self, path: str):
        self.path = Path(path)

    def write(self, tool_call: ToolCall, decision: AutoModeDecision) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": tool_call.tool_name,
            "path": tool_call.arguments.get("path") or tool_call.arguments.get("file_path"),
            "command": tool_call.executable_command or tool_call.arguments.get("command"),
            "tier": decision.tier.value,
            "verdict": decision.verdict.value,
            "reason": decision.reason,
            "consecutive_denials": decision.consecutive_denials,
            "total_denials": decision.total_denials,
            "escalated_to_human": decision.escalated_to_human,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
