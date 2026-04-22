# Review Notes

<!-- metadata: scope=review, audience=ai-assistants, topic=consistency-and-gaps -->

Consistency and completeness review of the generated documentation against the source code.

## Consistency Check

| Claim | Sources | Status |
|-------|---------|--------|
| 8 tools are registered | `server.py` (8 `mcp.tool(...)` calls), `interfaces.md`, `README.md` (8 names in `autoApprove`), `codebase_info.md` | ✅ consistent |
| Principle #10 = statelessness, no caching | `architecture.md`, `components.md`, `workflows.md`, enforced by `tests/test_statelessness.py` (docstring: "Principle #10: no caching") | ✅ consistent |
| `_MAX_SPAN_YEARS = 100`, `_MAX_STEP_ITERATIONS = 3650` | `server.py` constants, `architecture.md`, `components.md`, `interfaces.md` (error table) | ✅ consistent |
| Country code is case-insensitive | `server.py` (`.upper()` in `_get_country_holidays`), `tests/test_case_insensitive_country.py`, `architecture.md`, `interfaces.md` | ✅ consistent |
| Python `>=3.10`, CI matrix 3.10–3.13 | `pyproject.toml`, `.github/workflows/ci.yml`, `codebase_info.md`, `workflows.md` | ✅ consistent |
| `fastmcp >=2.12,<3` and `holidays >=0.50` | `pyproject.toml`, `.pre-commit-config.yaml` mypy hook, `dependencies.md` | ✅ consistent |
| `business_days_between` reports only weekday holidays in `holidays_in_range` | `server.py` (`if d in hols and not _is_weekend(d)`), `interfaces.md`, `data_models.md`, covered by `tests/test_aggregates.py::test_weekend_holiday_not_in_range` | ✅ consistent |
| `__version__ = "0.1.0"` | `__init__.py` and `pyproject.toml [project].version` | ⚠️ duplicated in two places — documented as "keep both in sync on release" in `components.md` and `workflows.md` |

No contradictions were found between the generated documents themselves or against the code.

## Completeness Check

### Well covered

- Tool surface (signatures, return shapes, errors) — `interfaces.md` + `data_models.md`.
- Architecture principles and dispatch flow — `architecture.md`.
- Test organization and fixture strategy — `codebase_info.md`, `components.md`.
- CI/release pipelines — `workflows.md`.
- Dependency roles and version rationale — `dependencies.md`.

### Gaps / areas with limited detail

1. **FastMCP internals**. The server relies on `mcp.run()` to choose stdio transport. If a maintainer wants to run over SSE/HTTP in the future, there's no guidance — because none exists in the code yet. (Not a gap in generated docs; a gap in the codebase itself. If added later, `architecture.md → "System View"` should be updated.)

2. **`get_current_date` clock behavior**. The function uses `datetime.datetime.now(tz=...)`, i.e., the process wall clock. This is documented implicitly via "Uses the process clock" but there is no explicit note about test strategies (mocking `datetime.datetime.now` is not currently done in the repo).

3. **Localization of holiday names**. Names come from the `holidays` library in the library's chosen locale per country (e.g., "Neujahr" for DE, "New Year's Day" for US). This is noted in `interfaces.md → list_holidays`, but there is no mechanism to request a specific locale — because `holidays.country_holidays` is called without a `language=` kwarg. Worth flagging as a known limitation.

4. **Per-country weekend customization**. Friday/Saturday weekend regions (e.g., many Middle East countries in `holidays`) are treated as Sat/Sun weekends here. Called out in `architecture.md → "What Is Deliberately Absent"` and `components.md → _is_weekend`. No test currently asserts behavior for such countries — tests exist only for DE and US (and a single Asia/Tokyo timezone test). Adding at least one weekend-customization edge-case test would close this gap.

5. **Coverage of `_country_display_name` fallbacks**. The three-level fallback (`country_name` → `__doc__` first line → code) is implemented, but the `test_metadata.py` tests assert only that each entry has `code` and `name` and contains known major countries. There is no targeted test for the doc-fallback or the final-fallback branches. Line-coverage likely exercises the common path only.

### Language-support limitations

This is a pure-Python codebase; there are no other languages to analyze. No cross-language inconsistencies apply.

## Recommendations

Purely documentation-maintenance recommendations (the code itself is outside scope of this SOP):

1. On any change to `src/business_day_mcp/server.py` tool signatures or return shapes, regenerate `interfaces.md` and `data_models.md` in the same PR.
2. On any dependency bump, regenerate `dependencies.md` — especially the version rationale table.
3. On any CI/release workflow change, regenerate `workflows.md`.
4. If Principle #10 (statelessness) is ever revisited, update `architecture.md`, `components.md`, and the `AGENTS.md` `Custom Instructions` note together. Do not relax `test_statelessness.py` without explicit sign-off.
5. Consider adding a CHANGELOG.md at the repo root — currently release notes come only from GitHub's auto-generator.

## Outstanding Questions for Maintainers

None blocking. The code is small, internally consistent, and the docs captured what the code currently guarantees.
