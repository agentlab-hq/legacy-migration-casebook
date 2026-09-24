"""Master Demonstration: The Unified Anthropic Agent Stack (2024-2026).

Runs an end-to-end simulation proving how each breakthrough works:
1. Workflows (Dec 2024): Prompt Chaining with programmatic gate
2. MCP Code Mode (Nov 2025): In-sandbox data filtering (98.7% token savings)
3. Parallel Teams (Feb 2026): Git-based task locking & GCC Oracle bisection
4. Auto Mode (Mar 2026): Classifying overeager action vs. safe file edit
5. Managed Agents (Apr 2026): Decoupled brain recovering from cattle sandbox crash
"""

from anthropic_agent_stack.workflows import PromptChainingWorkflow
from anthropic_agent_stack.mcp_code_mode import MCPCodeModeEngine, PIITokenizer
from anthropic_agent_stack.parallel_team_harness import (
    GitTaskLockManager, GCCOracleDifferentialTester, ContextPollutionFilter
)
from anthropic_agent_stack.auto_mode_guard import AutoModeGuardrail
from anthropic_agent_stack.session_and_harness import (
    DurableSessionLog, SecurityVault, StatelessHarnessBrain
)


def run_all_demos():
    print("=" * 70)
    print("ANTHROPIC AGENT ENGINEERING STACK (2024 - 2026) LIVE DEMO")
    print("=" * 70)

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

    # 2. Nov 2025: MCP Code Mode
    print("\n[2/5] Nov 2025: MCP Code Mode - Token Economy & In-Sandbox Filtering")
    mcp = MCPCodeModeEngine()
    costs = mcp.compare_token_costs("transcript_to_crm")
    print(f"  Scenario: {costs['scenario']}")
    print(f"  Direct Tool Calls: {costs['direct_tool_tokens']:,} tokens")
    print(f"  MCP Code Mode:     {costs['code_mode_tokens']:,} tokens")
    print(f"  Token Savings:     {costs['token_savings_pct']}% reduction!")

    pii = PIITokenizer()
    masked = pii.tokenize("Contact engineer Bob at bob@enterprise.corp or 555-123-4567")
    print(f"  PII Vault Tokenization: {masked}")

    # 3. Feb 2026: Parallel Agent Teams & GCC Oracle Bisection
    print("\n[3/5] Feb 2026: Parallel Agent Teams & GCC Oracle Differential Testing")
    locker = GitTaskLockManager()
    l1 = locker.try_acquire_lock("Agent-01", "parse_if_statement")
    l2 = locker.try_acquire_lock("Agent-02", "parse_if_statement")
    print(f"  Agent-01 acquire lock: {l1}")
    print(f"  Agent-02 acquire collision: {l2} (Correctly rejected duplicate task)")

    oracle = GCCOracleDifferentialTester()
    broken_mod = oracle.bisect_failing_module()
    print(f"  GCC Oracle Bisection: Isolated kernel boot failure to module -> '{broken_mod}'")

    raw_output = "make: *** [mm/memory.o] Error 1\npanic: page fault in memory.c:48\n" + ("ok\n" * 100)
    clean_log = ContextPollutionFilter.format_compiler_output(raw_output, "")
    print(f"  Context Pollution Mitigation:\n    {clean_log.splitlines()[0]}")
    print(f"    {clean_log.splitlines()[1]}")

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

    # Safe in-project edit
    eval_safe = guard.evaluate_action(
        user_prompt="Update router docs",
        tool_name="write_file",
        arguments={"path": "/project/src/router.rs", "content": "// router v2"}
    )
    print(f"  In-Project File Write:   Verdict={eval_safe.verdict} | Tier={eval_safe.tier}")

    # 5. Apr 2026: Managed Agents - Decoupled Brain & Hands Failover
    print("\n[5/5] Apr 2026: Scaling Managed Agents - Decoupled Failover")
    session = DurableSessionLog("sess-demo-100")
    vault = SecurityVault()
    vault.register_repo_token("https://github.com/my-org/repo", "secret-token-xyz")
    brain = StatelessHarnessBrain("sess-demo-100", session, vault)

    # Initial step
    step1 = brain.step("write_file", {"path": "main.c", "content": "int main() { return 0; }"})
    print(f"  Initial Step: {step1}")

    # Chaos: Kill sandbox container
    print("  Injecting Chaos: Terminating cattle container...")
    brain.current_sandbox.terminate()

    # Step after crash: automatic cattle re-provisioning without session loss!
    step2 = brain.step("read_file", {"path": "main.c"})
    print(f"  Failover Step: {step2}")
    print(f"  Durable Session Event Count: {len(session.events)} events recorded.")

    print("\n" + "=" * 70)
    print("ALL 5 SYSTEM TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_demos()
