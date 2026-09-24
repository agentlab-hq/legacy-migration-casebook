# Legacy Migration Casebook

## Agent Engineering Master Lab

This repository contains a project-owned reference implementation for building safer, more reliable, and more economical software agents. It combines deterministic workflow patterns, code-mode tool projections, parallel-agent coordination, automatic safety gates, durable sessions, and an interactive browser lab.

## What is included

- **Interactive lab:** `index.html` and `agent_lab/public/index.html` provide a browser-based dashboard for workflow, tool-economics, parallel-team, safety, and failover demonstrations.
- **Workflow engine:** `anthropic_agent_stack/workflows.py` implements prompt chaining, routing, parallelization, orchestrator-workers, and evaluator-optimizer patterns.
- **Code-mode engine:** `anthropic_agent_stack/mcp_code_mode.py` demonstrates progressive tool disclosure, in-sandbox filtering, reusable tool registration, and deterministic PII tokenization.
- **Parallel team harness:** `anthropic_agent_stack/parallel_team_harness.py` provides task locking, context-pollution filtering, time-blindness sampling, and differential oracle simulation.
- **Safety controls:** `anthropic_agent_stack/auto_mode_guard.py` and `claude_auto_mode/` implement injection screening, project boundaries, allowlists, policy rules, and deny-and-continue decisions.
- **Durable execution:** `anthropic_agent_stack/session_and_harness.py` models a stateless coordinator, disposable execution environments, an external credential vault, and replayable session events.
- **Commercial calculators:** `commercial_engine/` contains migration-oracle and return-on-investment prototypes.
- **Documentation:** `docs/` contains the engineering playbook and business roadmap.
- **Tests:** `tests/test_agent_stack.py` exercises the main safety, workflow, cost, locking, and failover behaviors.

## Quick start

Run the integrated demonstration:

```bash
python3 -m anthropic_agent_stack.run_integrated_system
```

Run the test suite:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Open the dashboard locally:

```bash
python3 -m http.server 8000
```

Then visit <http://localhost:8000/>.

## Repository principles

The project is kept self-contained in this repository. It uses the Python standard library for the reference stack, keeps safety decisions explicit and testable, and treats documentation, demos, and verification code as one coherent project.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
