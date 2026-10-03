"""CLI entry point for Markdown policy audit reports."""

import argparse
import sys
from typing import Optional, Sequence

from .report import load_audit_records, render_markdown_report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-policy-report")
    parser.add_argument("--audit-log", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        report = render_markdown_report(load_audit_records(args.audit_log))
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(report)
        else:
            print(report, end="")
    except (OSError, ValueError) as exc:
        print(f"agent-policy-report: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
