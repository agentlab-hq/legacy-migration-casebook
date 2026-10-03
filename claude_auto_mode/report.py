"""Human-readable summaries for JSONL policy audit logs."""

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def load_audit_records(path: str) -> List[Dict[str, Any]]:
    records = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on audit log line {line_number}: {exc.msg}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"Audit log line {line_number} must be a JSON object.")
        records.append(record)
    return records


def render_markdown_report(records: List[Dict[str, Any]]) -> str:
    verdicts = Counter(record.get("verdict", "UNKNOWN") for record in records)
    blocked = [record for record in records if record.get("verdict") == "BLOCK"]
    lines = [
        "# Agent Policy Report",
        "",
        f"- Decisions evaluated: {len(records)}",
        f"- Allowed: {verdicts['ALLOW']}",
        f"- Blocked: {verdicts['BLOCK']}",
        "",
        "## Blocked actions",
        "",
    ]
    if not blocked:
        lines.append("No actions were blocked.")
    else:
        lines.extend(["| Tool | Action | Reason |", "| --- | --- | --- |"])
        for record in blocked:
            action = record.get("command") or record.get("path") or "—"
            reason = str(record.get("reason", "—")).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {record.get('tool_name', '—')} | {action} | {reason} |")
    return "\n".join(lines) + "\n"
