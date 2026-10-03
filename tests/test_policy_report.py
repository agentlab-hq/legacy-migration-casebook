"""Tests for Markdown policy reports."""

import tempfile
import unittest
from pathlib import Path

from claude_auto_mode.report import load_audit_records, render_markdown_report


class TestPolicyReport(unittest.TestCase):
    def test_renders_decision_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            path.write_text(
                '{"tool_name":"bash","command":"git push origin main","verdict":"BLOCK","reason":"BR-01"}\n'
                '{"tool_name":"read_file","path":"README.md","verdict":"ALLOW","reason":"safe"}\n',
                encoding="utf-8",
            )
            report = render_markdown_report(load_audit_records(str(path)))

        self.assertIn("Decisions evaluated: 2", report)
        self.assertIn("Allowed: 1", report)
        self.assertIn("Blocked: 1", report)
        self.assertIn("git push origin main", report)

    def test_rejects_malformed_audit_log(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            path.write_text("not json\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_audit_records(str(path))


if __name__ == "__main__":
    unittest.main()
