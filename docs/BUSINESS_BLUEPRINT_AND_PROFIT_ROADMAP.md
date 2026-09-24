# Commercial Blueprint: Agent Engineering and Modernization

## Executive position

The project provides a human-gated engineering system for modernizing software and operating agentic workflows. It does not promise unsupervised production changes. Instead, it combines automation with explicit safety boundaries, reproducible verification, and senior-engineer review.

> Nothing merges without an accountable engineer reviewing the change.

## Product capabilities

### 1. Human-gated modernization

The workflow engine supports bounded modernization work inside disposable execution environments. Each task can be decomposed into small steps, checked by programmatic gates, and delivered as a reviewable change with test evidence.

### 2. Tool and token efficiency

The code-mode engine models progressive tool discovery and in-sandbox filtering. Large intermediate datasets can be reduced before they reach the model context, while deterministic tokenization protects sensitive identifiers during processing.

### 3. Parallel engineering teams

The parallel harness coordinates independent workers through task locks, reduces noisy compiler output, samples long-running checks, and uses differential oracles to isolate failing modules.

### 4. Safety and policy enforcement

The safety stack evaluates tool calls against project boundaries, safe-tool allowlists, injection probes, destructive-action rules, and retry budgets. The result is an explicit allow, deny, or review decision rather than an opaque side effect.

### 5. Durable managed execution

The session harness separates coordination state from disposable execution environments. Durable events can be replayed after a sandbox failure, while credentials remain in an external vault abstraction rather than being placed in the workspace.

## Potential offerings

| Offering | Customer outcome | Initial delivery |
| --- | --- | --- |
| Modernization pilot | A bounded, tested improvement to a legacy module | Scope review, isolated run, change report, tests |
| Agent-efficiency audit | Lower context overhead and clearer tool boundaries | Token-cost baseline, code-mode design, savings report |
| Safety architecture review | Safer agent execution for engineering teams | Policy review, project boundary design, verification plan |
| Managed-agent prototype | Recoverable multi-agent execution | Durable session model, sandbox lifecycle, failover demo |

## Delivery principles

- Start with a bounded module or workflow.
- Keep the customer’s main branch protected.
- Produce reviewable changes and reproducible test output.
- Treat credentials and external side effects as separate security boundaries.
- Measure cost, latency, reliability, and regression risk rather than relying on marketing claims.

## Current repository deliverables

- `index.html` — interactive browser lab.
- `anthropic_agent_stack/` — reference engineering stack.
- `claude_auto_mode/` — policy and safety modules.
- `commercial_engine/` — migration and ROI prototypes.
- `tests/` — executable verification suite.
- `docs/AGENT_ENGINEERING_PLAYBOOK_2024_2026.md` — architecture and engineering narrative.

## Next milestones

1. Expand tests around session replay (package configuration and CI already in place: `pyproject.toml` + `.github/workflows/ci.yml` covering the test suite, integrated demo, and both CLIs on Python 3.9–3.12).
2. Replace simulation-only integrations with configurable adapters.
3. Add structured JSON reports for migration runs and cost audits.
4. Document deployment boundaries for local, containerized, and hosted execution.
