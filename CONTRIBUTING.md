# Contributing to business-day-mcp

Thanks for your interest in improving business-day-mcp. Contributions of all sizes — bug reports, fixes, tests, and docs — are welcome.

## Getting started

Requirements: Python >= 3.10 and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/fbdo/business-day-mcp.git
cd business-day-mcp
uv sync --all-extras
```

Optionally install the pre-commit hooks:

```bash
uv run pre-commit install
```

## Project layout

- `src/business_day_mcp/` — package source (MCP server, tools).
- `tests/` — pytest test suite.
- `.github/workflows/` — CI (`ci.yml`) and release (`publish.yml`) pipelines.

## Build

The build backend is hatchling. Produce a wheel and sdist in `dist/`:

```bash
uv build
```

## Test

Tests live in `tests/` and run with pytest:

```bash
uv run pytest
```

A 90% coverage gate is enforced (configured in `pyproject.toml`); PRs that drop coverage below the threshold will fail CI.

## Code quality

Lint and format with ruff (target py310):

```bash
uv run ruff check .
uv run ruff format .
```

Type-check with mypy (strict, `python_version = 3.10`):

```bash
uv run mypy src
```

Run all pre-commit hooks across the repo:

```bash
uv run pre-commit run --all-files
```

The secrets baseline lives at `.secrets.baseline`; update it via `detect-secrets` if you intentionally add new detector-flagged strings.

## Reporting issues

File bugs and feature requests at <https://github.com/fbdo/business-day-mcp/issues>. Please include:

- Reproduction steps (minimal example if possible).
- Expected vs. actual behavior.
- Environment: OS, Python version, `business-day-mcp` version.
- Relevant logs or stack traces.

## Submitting changes

1. Fork the repo and create a topic branch, e.g. `feat/<short-description>` or `fix/<issue-number>`.
2. Keep PRs focused — one logical change per PR.
3. Include tests for new behavior and bug fixes.
4. Make sure CI passes locally before pushing:
   ```bash
   uv run ruff check .
   uv run mypy src
   uv run pytest
   ```
5. Write clear commit messages and reference related issues (e.g. `Fixes #123`).
6. Open the PR against `main` and respond to review feedback.

## Code of conduct / license

By contributing, you agree that your contributions are licensed under the MIT License, per the [`LICENSE`](./LICENSE) file.
