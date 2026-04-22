# AGENTS.md — business-day-mcp

<!-- metadata: role=agent-navigation-map, audience=ai-coding-assistants -->

A navigation map for AI coding assistants. For deeper reference, open the per-topic files under `.agents/summary/` (start with `.agents/summary/index.md`).

## Table of Contents

- [What this repo is](#what-this-repo-is) — one-paragraph scope
- [Directory Map](#directory-map) — where code lives
- [Key Entry Points](#key-entry-points) — start here when tracing behavior
- [Subsystems](#subsystems) — brief per-area summaries with file pointers
- [Repo-Specific Patterns](#repo-specific-patterns) — things that deviate from Python defaults
- [Config Files Worth Knowing](#config-files-worth-knowing) — what each file controls
- [Safety Invariants](#safety-invariants) — do-not-break rules
- [Custom Instructions](#custom-instructions) — human-maintained operational notes

## What this repo is

An MCP (Model Context Protocol) server that exposes 8 read-only tools for business-day and holiday arithmetic across 60+ countries. Single Python package, stdio transport via FastMCP, all country knowledge delegated to the `holidays` library.

## Directory Map

```
business-day-mcp/
├── src/business_day_mcp/
│   ├── server.py          # ★ all tool logic + helpers (single source of behavior)
│   ├── __init__.py        # re-exports main, mcp, __version__
│   └── __main__.py        # `python -m business_day_mcp` shim
├── tests/                 # one file per concern — see Subsystems
├── .github/workflows/
│   ├── ci.yml             # lint / typecheck / security / test matrix / build
│   └── publish.yml        # tag-triggered PyPI publish via Trusted Publisher
├── .agents/summary/       # generated per-topic docs (see index.md)
├── pyproject.toml         # deps + all tool config (ruff/mypy/pytest/bandit/coverage)
├── .pre-commit-config.yaml
├── .secrets.baseline      # detect-secrets baseline
└── uv.lock                # committed lockfile
```

## Key Entry Points

| Question | Open |
|----------|------|
| "How is the server started?" | `src/business_day_mcp/server.py → main()` (calls `mcp.run()`, stdio) |
| "What tools exist?" | `server.py` — search for `mcp.tool(` (8 registrations) |
| "What's the CLI command?" | `pyproject.toml → [project.scripts]` → `business-day-mcp` |
| "What's the response shape of tool X?" | `.agents/summary/interfaces.md` |
| "Why isn't there a cache?" | `.agents/summary/architecture.md` → Principle #10 |

## Subsystems

### MCP tools (`src/business_day_mcp/server.py`)

The entire runtime is one file. It defines a global `mcp = FastMCP("business-day-mcp")`, eight public tool functions, private helpers, and `main()`. Tools are registered imperatively with `mcp.tool(fn)` after each definition (no `@decorator` syntax in this repo). The eight tools:

```
is_business_day, get_current_date, next_business_day, previous_business_day,
last_business_day_of_month, business_days_between, list_holidays, get_supported_countries
```

Deep dive: `.agents/summary/components.md` and `.agents/summary/interfaces.md`.

### Tests (`tests/`)

One file per concern. `conftest.py` exposes DE/US 2026 reference-date fixtures — extend those before hardcoding dates in new tests.

| File | Covers |
|------|--------|
| `test_basic_tools.py` | `is_business_day`, `get_current_date` |
| `test_navigation.py` | `next_/previous_business_day` |
| `test_aggregates.py` | `business_days_between`, `last_business_day_of_month` |
| `test_metadata.py` | `list_holidays`, `get_supported_countries` |
| `test_edge_cases.py` | tz edges, US/DE holiday-on-weekend observance |
| `test_case_insensitive_country.py` | country `.upper()` normalization |
| `test_statelessness.py` | Principle #10 — **do not delete; monkeypatches `holidays.country_holidays` to enforce no caching** |

### CI / release (`.github/workflows/`)

`ci.yml` runs lint (`ruff check` + format), typecheck (`mypy src`), security (`bandit` + `pip-audit --strict` + `detect-secrets`), test matrix (pytest 3.10–3.13), then `build`.

`publish.yml` triggers on `v*.*.*` tags and publishes to PyPI via **OIDC Trusted Publisher** — there are no PyPI API tokens stored as secrets. First-time setup requires registering the repo at pypi.org (see comment at the top of `publish.yml`).

## Repo-Specific Patterns

- **Imperative tool registration**: `mcp.tool(fn)` is called on a separate line after each function definition. Preserve this style when adding tools; do not switch to `@mcp.tool` decorators.
- **Statelessness (Principle #10)**: `holidays.country_holidays(...)` is called fresh on every tool invocation. No memoization, no LRU, no module-level cache. Enforced by `tests/test_statelessness.py`. If you ever need caching, update the test and `.agents/summary/architecture.md` in the same change.
- **DoS guards**: `_MAX_SPAN_YEARS = 100` (used by `business_days_between`) and `_MAX_STEP_ITERATIONS = 3650` (used by `_step_business_day`). Both raise `ValueError`. Keep them.
- **Case-insensitive country**: `_get_country_holidays` calls `.upper()` on input; responses echo the normalized code. Callers may pass any case.
- **Weekend is Sat/Sun only**: No per-country weekend override exists. This is deliberate — see `.agents/summary/architecture.md → What Is Deliberately Absent`.
- **Errors are `ValueError`**: All validation failures raise `ValueError` with actionable messages. FastMCP serializes these as tool errors. No custom exception hierarchy.
- **Plain `dict[str, Any]` responses**: No Pydantic, no TypedDict. If you add a tool, follow the existing pattern.
- **Version duplicated**: `__version__` in `src/business_day_mcp/__init__.py` must be bumped in lockstep with `pyproject.toml → [project].version` on release.
- **Pre-commit mypy pins**: `.pre-commit-config.yaml` re-declares `fastmcp` and `holidays` under the mypy hook's `additional_dependencies`. Keep those constraints in sync with `pyproject.toml`.

## Config Files Worth Knowing

| File | Controls |
|------|----------|
| `pyproject.toml` | Deps, build backend (hatchling), ruff rules (E/F/W/I/B/UP/S/C90/SIM/RUF, line 100, mccabe 10), mypy strict on `src`, pytest with `--cov-fail-under=90` + `--strict-markers`, coverage branch mode, bandit exclusion of `tests/`. |
| `.pre-commit-config.yaml` | ruff (fix + format), mypy, bandit, detect-secrets, whitespace/yaml/toml hygiene. |
| `.secrets.baseline` | detect-secrets baseline — regenerate with `uv run detect-secrets scan > .secrets.baseline` if it flags a legitimate change. |
| `.github/workflows/ci.yml` | Full pipeline description; source of truth for what "green" means. |
| `.github/workflows/publish.yml` | Release path. Has a header comment requiring one-time PyPI Trusted Publisher setup. |
| `uv.lock` | Committed. Regenerate only on dependency changes (`uv lock`). |
| `tests/conftest.py` | Reference-date fixtures with a documented DE 2026 calendar block at the top — read it before adding tests that need known holidays. |

## Safety Invariants

Do not violate these without explicit sign-off — each has a test or review process guarding it:

1. `holidays.country_holidays` is called on every tool invocation (Principle #10).
2. `_MAX_SPAN_YEARS` and `_MAX_STEP_ITERATIONS` remain enforced (SR-F4).
3. Country input is `.upper()`-normalized before lookup.
4. All tools remain read-only and side-effect-free (reflected in README's `autoApprove` list).
5. Tests must stay ≥90% branch coverage (`pytest` fail-under in `pyproject.toml`).

## Custom Instructions

<!-- This section is for human and agent-maintained operational knowledge.
     Add repo-specific conventions, gotchas, and workflow rules here.
     This section is preserved exactly as-is when re-running codebase-summary. -->
