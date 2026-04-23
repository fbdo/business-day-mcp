# business-day-mcp

MCP server for business-day arithmetic with country-aware holiday calendars (fastmcp + holidays).

## What is this?

`business-day-mcp` exposes business-day math — "is today a business day?", "next business day after X", "how many business days between A and B?" — as tools an MCP client can call. Holiday calendars are provided by the [`holidays`](https://pypi.org/project/holidays/) library and cover 60+ countries, with optional regional subdivisions. It is intended for use with MCP clients such as Claude Desktop, Kiro, and any other tool that speaks the Model Context Protocol. Requires Python >= 3.10.

Example questions it can answer:

- Is today a business day in Germany?
- When is the last business day of April 2026?
- How many business days between Apr 21 and May 5 in the US?

## Features / Tools

- `get_current_date` — current date in a given IANA timezone.
- `is_business_day` — check whether a date is a business day for a country (+ optional subdivision).
- `next_business_day` / `previous_business_day` — step forward/backward by N business days.
- `last_business_day_of_month` — last business day of a given month.
- `business_days_between` — count business days between two dates.
- `list_holidays` — holidays for a country/year (+ optional subdivision).
- `get_supported_countries` — supported ISO 3166-1 alpha-2 codes and their subdivisions.
- `get_supported_subdivisions` — subdivisions and aliases for a single country.

All tools are read-only and safe to auto-approve.

## Install

### From the package

```bash
uvx business-day-mcp
```

Or persistent install:

```bash
pip install business-day-mcp
```

Run the server:

```bash
business-day-mcp
# or
python -m business_day_mcp
```

### From source

```bash
git clone https://github.com/fbdo/business-day-mcp.git
cd business-day-mcp
uv sync --all-extras
uv run business-day-mcp
```

Run the test suite (coverage must stay ≥ 90%):

```bash
uv run pytest
```

## Configure

Add to your `mcp.json`:

```jsonc
{
  "mcpServers": {
    "business-day-mcp": {
      "command": "uvx",
      "args": ["business-day-mcp"],
      "autoApprove": [
        "get_current_date",
        "is_business_day",
        "next_business_day",
        "previous_business_day",
        "last_business_day_of_month",
        "business_days_between",
        "list_holidays",
        "get_supported_countries",
        "get_supported_subdivisions"
      ]
    }
  }
}
```

### From a local clone

Run `uv sync --all-extras` in the cloned repo first, then replace `/absolute/path/to/business-day-mcp` below with the clone's absolute path (you can copy the same `autoApprove` array from the package example above if desired):

```json
{
  "mcpServers": {
    "business-day": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/business-day-mcp",
        "run",
        "business-day-mcp"
      ]
    }
  }
}
```

## Conventions

- Dates: ISO 8601 strings (`YYYY-MM-DD`).
- Countries: ISO 3166-1 alpha-2 codes (`DE`, `US`, `GB`, ...) — case-insensitive.
- Timezones: IANA names (`Europe/Berlin`, `America/New_York`, ...).
- Subdivisions (optional): country-specific region codes (`BY` for Bavaria, `CA` for California, ...). Case-sensitive — pass exactly as returned by `get_supported_countries`. Omit to get nation-wide holidays only.

Regional subdivisions: all country-aware tools (`is_business_day`, `next_business_day`, `previous_business_day`, `last_business_day_of_month`, `business_days_between`, `list_holidays`) accept an optional `subdiv` parameter. Example: `country="DE", subdiv="BY"` treats Epiphany (Jan 6) as a holiday in Bavaria. Discover valid codes via `get_supported_countries` (returns a `subdivisions: list[str]` per country; `[]` for countries without regional variants, e.g. `JP`). For a single-country lookup that also includes alias names (e.g. `"Bavaria"` → `"BY"`), use `get_supported_subdivisions(country="DE")` — returns `{subdivisions: ["BY", ...], aliases: {"Bavaria": "BY", ...}}`.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for build, test, issue, and pull request guidelines. The project repo is at <https://github.com/fbdo/business-day-mcp>.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
