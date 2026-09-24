"""Comprehensive unit tests for the Anthropic Agent Engineering Stack."""

import unittest
from anthropic_agent_stack.workflows import (
    PromptChainingWorkflow, RoutingWorkflow, ParallelizationWorkflow,
    OrchestratorWorkersWorkflow, EvaluatorOptimizerWorkflow
)
from anthropic_agent_stack.mcp_code_mode import MCPCodeModeEngine, PIITokenizer
from anthropic_agent_stack.parallel_team_harness import (
    GitTaskLockManager, GCCOracleDifferentialTester, ContextPollutionFilter, TimeBlindnessTestSampler
)
from anthropic_agent_stack.auto_mode_guard import AutoModeGuardrail
from anthropic_agent_stack.types import DecisionVerdict, DecisionTier
from anthropic_agent_stack.session_and_harness import (
    DurableSessionLog, SecurityVault, StatelessHarnessBrain
)


class TestAnthropicAgentStack(unittest.TestCase):

    def test_prompt_chaining_gate(self):
        steps = [
            {"name": "s1", "fn": lambda x: x + " -> step1", "gate_fn": lambda x: ("step1" in x, "ok")},
            {"name": "s2", "fn": lambda x: x + " -> step2", "gate_fn": lambda x: (True, "ok")}
        ]
        chain = PromptChainingWorkflow(steps)
        res = chain.run("start")
        self.assertTrue(res["success"])
        self.assertEqual(res["final_output"], "start -> step1 -> step2")

    def test_routing(self):
        router = RoutingWorkflow(
            router_fn=lambda q: "billing" if "invoice" in q else "tech",
            routes={"billing": lambda q: "Processed billing", "tech": lambda q: "Processed tech"}
        )
        res = router.run("Where is my invoice?")
        self.assertEqual(res["selected_route"], "billing")

    def test_mcp_token_savings(self):
        engine = MCPCodeModeEngine()
        costs = engine.compare_token_costs("transcript_to_crm")
        self.assertGreater(costs["token_savings_pct"], 95.0)

    def test_pii_vault_tokenizer(self):
        vault = PIITokenizer()
        raw = "Send note to john@example.com at 555-444-3333"
        masked = vault.tokenize(raw)
        self.assertNotIn("john@example.com", masked)
        self.assertIn("[EMAIL_1]", masked)
        unmasked = vault.detokenize(masked)
        self.assertEqual(unmasked, raw)

    def test_git_task_locking(self):
        locker = GitTaskLockManager()
        self.assertTrue(locker.try_acquire_lock("Agent-A", "parse_expr"))
        self.assertFalse(locker.try_acquire_lock("Agent-B", "parse_expr"))
        locker.release_lock("Agent-A", "parse_expr")
        self.assertTrue(locker.try_acquire_lock("Agent-B", "parse_expr"))

    def test_gcc_oracle_bisection(self):
        oracle = GCCOracleDifferentialTester()
        failing_mod = oracle.bisect_failing_module()
        self.assertEqual(failing_mod, "mm/memory.c")

    def test_auto_mode_overeager_blocking(self):
        guard = AutoModeGuardrail(project_root="/project")
        res = guard.evaluate_action(
            user_prompt="Clean up",
            tool_name="bash",
            arguments={"command": "git push origin --delete dev"}
        )
        self.assertEqual(res.verdict, DecisionVerdict.BLOCK)
        self.assertEqual(res.consecutive_denials, 1)

    def test_auto_mode_safe_tier1(self):
        guard = AutoModeGuardrail(project_root="/project")
        res = guard.evaluate_action(
            user_prompt="Find function",
            tool_name="read_file",
            arguments={"path": "src/main.py"}
        )
        self.assertEqual(res.verdict, DecisionVerdict.ALLOW)
        self.assertEqual(res.tier, DecisionTier.TIER_1_SAFE_ALLOWLIST)

    def test_managed_agents_failover(self):
        session = DurableSessionLog("sess-test")
        vault = SecurityVault()
        brain = StatelessHarnessBrain("sess-test", session, vault)
        
        # Test lazy provisioning & execution
        out = brain.step("write_file", {"path": "test.txt", "content": "hello"})
        self.assertIn("Wrote 5 bytes", out)
        
        # Simulate container crash
        brain.current_sandbox.terminate()
        
        # Step should recover by provisioning fresh container
        out2 = brain.step("bash", {"command": "echo test"})
        self.assertIn("Executed", out2)
        self.assertTrue(brain.current_sandbox.alive)
        restored = brain.step("read_file", {"path": "test.txt"})
        self.assertEqual(restored, "hello")


if __name__ == "__main__":
    unittest.main()
