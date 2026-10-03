# Contributing

Thanks for helping make AI coding agents safer.

## Getting started

1. Fork the repository and create a focused branch.
2. Run the full test suite:

   ```bash
   python -m unittest discover -s tests -p "test_*.py" -v
   ```

3. Keep changes small, document behavior changes, and add regression tests for every policy rule or bypass fix.

## Good first contributions

Look for issues labeled `good first issue`, improve presets, add safely-scoped policy rules, or contribute real integration examples.

## Pull requests

Explain the user problem, the safety trade-off, and how you tested the change. Never include real credentials, private logs, or production data in issues or pull requests.
