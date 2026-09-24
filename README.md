# Legacy Migration Casebook

A project-owned workspace for documenting, testing, and improving migrations of legacy software.

## Purpose

This repository is the single home for the project. It will contain migration plans, implementation changes, compatibility checks, regression tests, and lessons learned from modernizing existing codebases.

The project is organized around a practical workflow:

1. Describe the legacy system and its constraints.
2. Define the intended modernization in small, reviewable steps.
3. Implement the change with tests and compatibility checks.
4. Record regressions, fixes, and decisions.
5. Keep the final implementation and documentation together in this repository.

## Repository status

The repository has been reset to a clean foundation. No external migration case study or upstream project is included. New project-specific source code and documentation should be added here as the work is defined.

## Suggested structure

```text
.
├── README.md
├── docs/            # Project documentation and migration decisions
├── src/             # Application or library source code
├── tests/           # Automated tests
└── scripts/         # Reproducible development and verification helpers
```

Directories will be added when their contents are needed.

## Development principles

- Keep changes small, explicit, and reviewable.
- Preserve documented compatibility requirements.
- Add a regression test for every discovered bug.
- Prefer reproducible commands over undocumented manual steps.
- Keep project-specific work and documentation in this repository.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
