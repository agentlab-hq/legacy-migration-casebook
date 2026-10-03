# Agent Policy Gate

> Open-source safety controls for AI coding agents.

Define what an agent may do, block unsafe actions before they run, and keep an auditable record for every decision. Agent Policy Gate is a lightweight Python policy layer and reusable GitHub Action for teams adopting coding agents.

## Why it exists

Coding agents can read, edit, test, and ship software quickly. They should not silently force-push history, alter secrets, deploy production changes, or send data outside approved boundaries. This project gives teams a clear, testable control point between an agent's proposed action and execution.

## Start in 60 seconds

```bash
git clone https://github.com/agentlab-hq/legacy-migration-casebook.git
cd legacy-migration-casebook
pip install .
agent-policy --config examples/presets/ci-review.json --tool-name bash --command "git push origin main"
```

The command prints a JSON decision and exits with `0` for an allowed action, `2` for a blocked action, or `3` for invalid input/configuration.

## What you get

- **Policy CLI:** evaluate commands and project file edits with `agent-policy`.
- **Safe defaults:** project boundaries, sensitive-file protections, prompt-injection scanning, and dangerous-command rules.
- **Audit trail:** append decisions to JSONL logs, then render a Markdown report with `agent-policy-report`.
- **Adoption presets:** [safe local development](examples/presets/safe-local-development.json), [CI review](examples/presets/ci-review.json), and [production restricted](examples/presets/production-restricted.json).
- **GitHub Actions integration:** use the reusable action in [`.github/actions/agent-policy`](.github/actions/agent-policy/action.yml).
- **Reference lab:** workflow, tool-economics, durable-session, and safety-pattern demonstrations.

## GitHub Actions

```yaml
- uses: ./.github/actions/agent-policy
  with:
    config: examples/presets/ci-review.json
    tool-name: bash
    command: git push origin feature/example
```

The action creates a JSONL audit log and a Markdown report that your workflow can upload as an artifact.

## Configuration

Start from a preset and tailor trusted organizations, domains, project boundaries, and narrowly scoped custom allows. Never add credentials or production secrets to policy files.

## Development

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m anthropic_agent_stack.run_integrated_system
```

## Community

- Read [CONTRIBUTING.md](CONTRIBUTING.md) to contribute.
- Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).
- Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- See the public [roadmap](docs/ROADMAP.md).

## License

MIT. See [LICENSE](LICENSE).
