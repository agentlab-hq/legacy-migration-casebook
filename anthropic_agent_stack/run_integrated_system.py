"""Master Demonstration: The Unified Anthropic Agent Stack (2024-2026).

Runs an end-to-end simulation proving how each breakthrough works:
1. Workflows (Dec 2024): Prompt Chaining with programmatic gate
2. MCP Code Mode (Nov 2025): In-sandbox data filtering (98.8% token savings)
3. Parallel Teams (Feb 2026): Git-based task locking & GCC Oracle bisection
4. Auto Mode (Mar 2026): Classifying overeager action vs. safe file edit
5. Managed Agents (Apr 2026): Decoupled brain recovering from cattle sandbox crash

Every stage is asserted; any failure prints a clear message and exits non-zero.
"""

import shutil
import sys
import tempfile

from anthropic_agent_stack.workflows import PromptChainingWorkflow
from anthropic_agent_stack.mcp_code_mode import MCPCodeModeEngine, PIITokenizer
from anthropic_agent_stack.parallel_team_harness import (
    GitTaskLockManager, GCCOracleDifferentialTester, ContextPollutionFilter
)
from anthropic_agent_stack.auto_mode_guard import AutoModeGuardrail
from anthropic_agent_stack.session_and_harness import (
    DurableSessionLog, SecurityVault, StatelessHarnessBrain
)
from anthropic_agent_stack.types import DecisionTier, DecisionVerdict


def check(condition: bool, label: str):
    if not condition:
        raise AssertionError(f"stage check failed: {label}")


def run_all_demos() -> bool:
    print("=" * 70)
    print("ANTHROPIC AGENT ENGINEERING STACK (2024 - 2026) LIVE DEMO")
    print("=" * 70)
    lock_dir = tempfile.mkdtemp(prefix="current_tasks_demo_")
    try:
        return _run_all(lock_dir)
    finally:
        shutil.rmtree(lock_dir, ignore_errors=True)


def _run_all(lock_dir: str) -> bool:
    # 1. Dec 2024: Prompt Chaining Workflow
    print("\n[1/5] Dec 2024: Workflows - Prompt Chaining with Gate")
    steps = [
        {
            "name": "Outline Generator",
            "fn": lambda topic: f"1. Architecture of {topic}\n2. Scaling Limits\n3. Safety",
            "gate_fn": lambda out: (len(out.splitlines()) >= 3, "Outline has at least 3 sections")
        },
        {
            "name": "Draft Expander",
            "fn": lambda outline: f"Verified Executive Report based on:\n{outline}",
            "gate_fn": lambda out: ("Report" in out, "Draft contains report title")
        }
    ]
    chain = PromptChainingWorkflow(steps)
    chain_res = chain.run("Autonomous Agents")
    print(f"  Result: Success={chain_res['success']}, Final Length={len(chain_res['final_output'])} chars")
    check(chain_res["success"] and len(chain_res["final_output"]) == 100, "prompt chaining succeeded with 100-char output")

    # 2. Nov 2025: MCP Code Mode
    print("\n[2/5] Nov 2025: MCP Code Mode - Token Economy & In-Sandbox Filtering")
    mcp = MCPCodeModeEngine()
    costs = mcp.compare_token_costs("transcript_to_crm")
    print(f"  Scenario: {costs['scenario']}")
    print(f"  Direct Tool Calls: {costs['direct_tool_tokens']:,} tokens")
    print(f"  MCP Code Mode:     {costs['code_mode_tokens']:,} tokens")
    print(f"  Token Savings:     {costs['token_savings_pct']}% reduction!")
    check(costs["direct_tool_tokens"] == 105000 and costs["code_mode_tokens"] == 1270, "transcript_to_crm token model")
    check(costs["token_savings_pct"] > 95.0, "savings above 95%")

    pii = PIITokenizer()
    masked = pii.tokenize("Contact engineer Bob at bob@enterprise.corp or 555-123-4567")
    print(f"  PII Vault Tokenization: {masked}")
    check(masked == "Contact engineer Bob at [EMAIL_1] or [PHONE_2]", "PII tokens assigned")
    check(pii.detokenize(masked) == "Contact engineer Bob at bob@enterprise.corp or 555-123-4567", "PII round-trip")

    # 3. Feb 2026: Parallel Agent Teams & GCC Oracle Bisection
    print("\n[3/5] Feb 2026: Parallel Agent Teams & GCC Oracle Differential Testing")
    locker = GitTaskLockManager(lock_dir=lock_dir)
    l1 = locker.try_acquire_lock("Agent-01", "parse_if_statement")
    l2 = locker.try_acquire_lock("Agent-02", "parse_if_statement")
    print(f"  Agent-01 acquire lock: {l1}")
    print(f"  Agent-02 acquire collision: {l2} (Correctly rejected duplicate task)")
    check(l1 is True and l2 is False, "atomic lock claim + collision rejection")
    check(locker.release_lock("Agent-02", "parse_if_statement") is False, "wrong owner cannot release")
    check(locker.release_lock("Agent-01", "parse_if_statement") is True, "owner releases lock")

    oracle = GCCOracleDifferentialTester()
    broken_mod = oracle.bisect_failing_module()
    print(f"  GCC Oracle Bisection: Isolated kernel boot failure to module -> '{broken_mod}'")
    check(broken_mod == "mm/memory.c", "oracle isolated the buggy module")

    raw_output = "make: *** [mm/memory.o] Error 1\npanic: page fault in memory.c:48\n" + ("ok\n" * 100)
    clean_log = ContextPollutionFilter.format_compiler_output(raw_output, "")
    print(f"  Context Pollution Mitigation:\n    {clean_log.splitlines()[0]}")
    print(f"    {clean_log.splitlines()[1]}")
    check(clean_log.startswith("Build Failed with 2 errors"), "compiler output summarized")

    # 4. Mar 2026: Claude Code Auto Mode
    print("\n[4/5] Mar 2026: Claude Code Auto Mode - Safety Gating without Prompts")
    guard = AutoModeGuardrail(project_root="/project")

    # Overeager incident: user says clean up, agent tries remote delete
    eval_danger = guard.evaluate_action(
        user_prompt="Clean up my branches",
        tool_name="bash",
        arguments={"command": "git push origin --delete main"}
    )
    print(f"  Overeager Branch Delete: Verdict={eval_danger.verdict} | Reason={eval_danger.reason}")
    check(eval_danger.verdict == DecisionVerdict.BLOCK, "overeager remote delete blocked")
    check("Clean up my branches" in eval_danger.stage2_reasoning, "user directive present in classifier reasoning")

    # Safe in-project edit
    eval_safe = guard.evaluate_action(
        user_prompt="Update router docs",
        tool_name="write_file",
        arguments={"path": "/project/src/router.rs", "content": "// router v2"}
    )
    print(f"  In-Project File Write:   Verdict={eval_safe.verdict} | Tier={eval_safe.tier}")
    check(
        eval_safe.verdict == DecisionVerdict.ALLOW and eval_safe.tier == DecisionTier.TIER_2_PROJECT_BOUNDARY,
        "in-project write allowed at Tier 2"
    )

    # Boundary violation: out-of-project write must be BLOCKED at Tier 2
    eval_escape = guard.evaluate_action(
        user_prompt="Move the config",
        tool_name="write_file",
        arguments={"path": "/elsewhere/config.yaml", "content": "x"}
    )
    print(f"  Out-of-Project Write:    Verdict={eval_escape.verdict} | Tier={eval_escape.tier}")
    check(
        eval_escape.verdict == DecisionVerdict.BLOCK and eval_escape.tier == DecisionTier.TIER_2_PROJECT_BOUNDARY,
        "out-of-project write blocked at Tier 2"
    )

    # 5. Apr 2026: Managed Agents - Decoupled Brain & Hands Failover
    print("\n[5/5] Apr 2026: Scaling Managed Agents - Decoupled Failover")
    session = DurableSessionLog("sess-demo-100")
    vault = SecurityVault()
    vault.register_repo_token("https://github.com/my-org/repo", "secret-token-xyz")
    brain = StatelessHarnessBrain("sess-demo-100", session, vault)

    # Initial step
    step1 = brain.step("write_file", {"path": "main.c", "content": "int main() { return 0; }"})
    print(f"  Initial Step: {step1}")
    check("Wrote 24 bytes to main.c" == step1, "initial write executed")

    # Chaos: Kill sandbox container
    print("  Injecting Chaos: Terminating cattle container...")
    brain.current_sandbox.terminate()

    # Step after crash: automatic cattle re-provisioning without session loss!
    step2 = brain.step("read_file", {"path": "main.c"})
    print(f"  Failover Step: {step2}")
    check(step2 == "int main() { return 0; }", "file state replayed into fresh cattle sandbox")
    check(brain.current_sandbox.alive, "new sandbox is alive")
    print(f"  Durable Session Event Count: {len(session.events)} events recorded.")
    check(len(session.events) >= 5, "durable session recorded the lifecycle")

    print("\n" + "=" * 70)
    print("ALL 5 SYSTEM TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        ok = run_all_demos()
    except AssertionError as exc:
        print(f"\nDEMO FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0 if ok else 1)
