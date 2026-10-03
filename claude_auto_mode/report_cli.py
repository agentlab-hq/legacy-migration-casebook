"""Command-line entry point for rendering policy audit reports."""

import argparse
import sys
from typing import Optional, Sequence

from .report import load_audit_records, render_markdown_report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-policy-report",
        description="Render a Markdown summary from an agent-policy JSONL audit log.",
    )
    parser.add_argument("--audit-log", required=True, help="Path to the JSONL audit log.")
    parser.add_argument("--output", help="Optional path for the Markdown report.")
    args = parser.parse_args(argv)

    try:
        report = render_markdown_report(load_audit_records(args.audit_log))
    except (OSError, ValueError) as exc:
        print(f"agent-policy-report: {exc}", file=sys.stderr)
        return 3

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(report)
        except OSError as exc:
            print(f"agent-policy-report: could not write report: {exc}", file=sys.stderr)
            return 3
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
