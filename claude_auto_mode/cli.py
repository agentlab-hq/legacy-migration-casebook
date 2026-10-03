"""Command-line adapter for enforcing Auto Mode policy decisions."""

import argparse
import json
import sys
from typing import Any, Dict, Optional, Sequence

from .audit import JsonlAuditLogger
from .config import load_runtime_config
from .pipeline import AutoModePipeline
from .types import ToolCall


def _arguments(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("--arguments must contain a JSON object.")
    return parsed


def _decision_payload(decision) -> Dict[str, Any]:
    return {
        "tier": decision.tier.value,
        "verdict": decision.verdict.value,
        "reason": decision.reason,
        "retry_feedback": decision.retry_feedback,
        "consecutive_denials": decision.consecutive_denials,
        "total_denials": decision.total_denials,
        "escalated_to_human": decision.escalated_to_human,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-policy",
        description="Evaluate a proposed tool call against the Auto Mode policy.",
    )
    parser.add_argument("--config", help="Path to a JSON policy configuration file.")
    parser.add_argument("--tool-name", required=True, help="Tool being evaluated, such as bash or write_file.")
    parser.add_argument("--command", help="Executable command for shell-like tools.")
    parser.add_argument("--path", help="Target path for file-edit tools.")
    parser.add_argument("--arguments", help="Additional tool arguments as a JSON object.")
    parser.add_argument("--user-prompt", default="", help="Authorization context for the decision.")
    parser.add_argument("--tool-output", default="", help="Untrusted prior tool output to scan for injection.")
    parser.add_argument("--audit-log", help="Append JSONL decision records to this path.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        runtime = (
            load_runtime_config(args.config)
            if args.config
            else {
                "project_root": "/project",
                "user_custom_allows": [],
                "policy_config": None,
                "audit_log": None,
            }
        )
        call_arguments = _arguments(args.arguments)
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 3

    if args.path:
        call_arguments["path"] = args.path
    if args.command:
        call_arguments["command"] = args.command

    tool_call = ToolCall(
        id="cli",
        tool_name=args.tool_name,
        arguments=call_arguments,
        executable_command=args.command,
    )
    pipeline = AutoModePipeline(
        project_root=runtime["project_root"],
        config=runtime["policy_config"],
        user_custom_allows=runtime["user_custom_allows"],
    )
    decision = pipeline.evaluate(tool_call, user_prompt=args.user_prompt, tool_output=args.tool_output)
    audit_path = args.audit_log or runtime["audit_log"]
    if audit_path:
        JsonlAuditLogger(audit_path).write(tool_call, decision)

    print(json.dumps(_decision_payload(decision), sort_keys=True))
    return 0 if decision.verdict.value == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
