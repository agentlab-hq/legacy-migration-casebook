"""Tests for the installable policy CLI and its JSONL audit trail."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from claude_auto_mode.cli import main


class TestPolicyCli(unittest.TestCase):
    def test_blocks_dangerous_command_and_writes_audit_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit_path = root / "audit" / "decisions.jsonl"
            config_path = root / "policy.json"
            config_path.write_text(
                json.dumps({"project_root": directory, "audit_log": str(audit_path)}),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--config", str(config_path),
                    "--tool-name", "bash",
                    "--command", "git push origin main",
                ])

            self.assertEqual(exit_code, 2)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["verdict"], "BLOCK")
            self.assertTrue(audit_path.exists())
            record = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(record["verdict"], "BLOCK")
            self.assertEqual(record["tool_name"], "bash")

    def test_allows_relative_project_edit_from_json_arguments(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main([
                "--tool-name", "write_file",
                "--arguments", json.dumps({"path": "src/main.py"}),
            ])

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["verdict"], "ALLOW")

    def test_rejects_invalid_config(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "policy.json"
            config_path.write_text(json.dumps({"user_custom_allows": "black ."}), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = main([
                    "--config", str(config_path),
                    "--tool-name", "bash",
                    "--command", "ls",
                ])

            self.assertEqual(exit_code, 3)
            self.assertIn("list of strings", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
