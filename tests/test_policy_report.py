"""Tests for Markdown reports generated from policy audit logs."""

import tempfile
import unittest
from pathlib import Path

from claude_auto_mode.report import load_audit_records, render_markdown_report


class TestPolicyReport(unittest.TestCase):
    def test_renders_blocked_action_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            audit_path = Path(directory) / "audit.jsonl"
            audit_path.write_text(
                '{"timestamp":"2026-10-03T00:00:00Z","tool_name":"bash","command":"git push origin main","tier":"Tier 3","verdict":"BLOCK","reason":"BR-01 direct push"}\n'
                '{"timestamp":"2026-10-03T00:01:00Z","tool_name":"read_file","path":"README.md","tier":"Tier 1","verdict":"ALLOW","reason":"safe"}\n',
                encoding="utf-8",
            )
            report = render_markdown_report(load_audit_records(str(audit_path)))

        self.assertIn("Decisions evaluated: 2", report)
        self.assertIn("Allowed: 1", report)
        self.assertIn("Blocked: 1", report)
        self.assertIn("git push origin main", report)

    def test_rejects_malformed_audit_record(self):
        with tempfile.TemporaryDirectory() as directory:
            audit_path = Path(directory) / "audit.jsonl"
            audit_path.write_text("not json\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_audit_records(str(audit_path))


if __name__ == "__main__":
    unittest.main()
