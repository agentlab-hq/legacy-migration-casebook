"""Comprehensive unit tests for the Anthropic Agent Engineering Stack."""

import tempfile
import unittest
from pathlib import Path

from anthropic_agent_stack.workflows import PromptChainingWorkflow, RoutingWorkflow
from anthropic_agent_stack.mcp_code_mode import MCPCodeModeEngine, PIITokenizer
from anthropic_agent_stack.parallel_team_harness import (
    GitTaskLockManager, GCCOracleDifferentialTester
)
from anthropic_agent_stack.auto_mode_guard import AutoModeGuardrail
from anthropic_agent_stack.types import DecisionVerdict, DecisionTier
from anthropic_agent_stack.session_and_harness import (
    DurableSessionLog, SecurityVault, StatelessHarnessBrain
)
from commercial_engine.migration_oracle import CommercialMigrationEngine, TestOracle


class TestAnthropicAgentStack(unittest.TestCase):
    def test_prompt_chaining_gate(self):
        steps = [
            {"name": "s1", "fn": lambda x: x + " -> step1", "gate_fn": lambda x: ("step1" in x, "ok")},
            {"name": "s2", "fn": lambda x: x + " -> step2", "gate_fn": lambda x: (True, "ok")}
        ]
        result = PromptChainingWorkflow(steps).run("start")
        self.assertTrue(result["success"])
        self.assertEqual(result["final_output"], "start -> step1 -> step2")

    def test_routing(self):
        router = RoutingWorkflow(
            router_fn=lambda q: "billing" if "invoice" in q else "tech",
            routes={"billing": lambda q: "Processed billing", "tech": lambda q: "Processed tech"}
        )
        self.assertEqual(router.run("Where is my invoice?")["selected_route"], "billing")

    def test_mcp_token_savings(self):
        costs = MCPCodeModeEngine().compare_token_costs("transcript_to_crm")
        self.assertGreater(costs["token_savings_pct"], 95.0)

    def test_pii_vault_tokenizer(self):
        vault = PIITokenizer()
        raw = "Send note to john@example.com at 555-444-3333"
        masked = vault.tokenize(raw)
        self.assertNotIn("john@example.com", masked)
        self.assertIn("[EMAIL_1]", masked)
        self.assertEqual(vault.detokenize(masked), raw)

    def test_git_task_locking(self):
        locker = GitTaskLockManager()
        self.assertTrue(locker.try_acquire_lock("Agent-A", "parse_expr"))
        self.assertFalse(locker.try_acquire_lock("Agent-B", "parse_expr"))
        locker.release_lock("Agent-A", "parse_expr")
        self.assertTrue(locker.try_acquire_lock("Agent-B", "parse_expr"))

    def test_gcc_oracle_bisection(self):
        self.assertEqual(GCCOracleDifferentialTester().bisect_failing_module(), "mm/memory.c")

    def test_auto_mode_overeager_blocking(self):
        result = AutoModeGuardrail(project_root="/project").evaluate_action(
            user_prompt="Clean up", tool_name="bash",
            arguments={"command": "git push origin --delete dev"}
        )
        self.assertEqual(result.verdict, DecisionVerdict.BLOCK)
        self.assertEqual(result.consecutive_denials, 1)

    def test_auto_mode_safe_tier1(self):
        result = AutoModeGuardrail(project_root="/project").evaluate_action(
            user_prompt="Find function", tool_name="read_file",
            arguments={"path": "src/main.py"}
        )
        self.assertEqual(result.verdict, DecisionVerdict.ALLOW)
        self.assertEqual(result.tier, DecisionTier.TIER_1_SAFE_ALLOWLIST)

    def test_auto_mode_rejects_traversal_and_prefix_escape(self):
        guard = AutoModeGuardrail(project_root="/project")
        for path in ("../outside.py", "/project-other/file.py"):
            result = guard.evaluate_action("edit", "write_file", {"path": path, "content": "x"})
            self.assertNotEqual(result.tier, DecisionTier.TIER_2_PROJECT_BOUNDARY)

    def test_auto_mode_allows_normalized_project_path(self):
        with tempfile.TemporaryDirectory() as root:
            path = str(Path(root) / "src" / "main.py")
            result = AutoModeGuardrail(project_root=root).evaluate_action(
                "edit", "write_file", {"path": path, "content": "x"}
            )
            self.assertEqual(result.tier, DecisionTier.TIER_2_PROJECT_BOUNDARY)

    def test_migration_oracle_rejects_invalid_code(self):
        passed, log = TestOracle.run_unit_tests("def broken(:\n    pass")
        self.assertFalse(passed)
        self.assertIn("SYNTAX_ERROR", log)

    def test_migration_engine_executes_smoke_tests(self):
        summary = CommercialMigrationEngine().execute_migration()
        self.assertEqual(summary["total_files"], 2)
        self.assertEqual(summary["verified_count"], 2)
        self.assertEqual(summary["regressions"], 0)

    def test_managed_agents_failover(self):
        session = DurableSessionLog("sess-test")
        brain = StatelessHarnessBrain("sess-test", session, SecurityVault())
        self.assertIn("Wrote 5 bytes", brain.step("write_file", {"path": "test.txt", "content": "hello"}))
        brain.current_sandbox.terminate()
        self.assertIn("Executed", brain.step("bash", {"command": "echo test"}))
        self.assertTrue(brain.current_sandbox.alive)
        self.assertEqual(brain.step("read_file", {"path": "test.txt"}), "hello")


if __name__ == "__main__":
    unittest.main()
