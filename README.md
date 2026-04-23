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

## Usage Examples

The examples below show typical agent questions and the actual JSON returned by the server. Dates reflect the real 2025/2026 calendars from the `holidays` library.

### Is this a business day?

> "Is July 4, 2025 a business day in the US?"

Tool call: `is_business_day(date="2025-07-04", country="US")`

```json
{
  "date": "2025-07-04",
  "country": "US",
  "is_business_day": false,
  "is_weekend": false,
  "is_holiday": true,
  "holiday_name": "Independence Day"
}
```

### Today's date in a specific timezone

> "What's today's date in New York?"

Tool call: `get_current_date(timezone="America/New_York")`

```json
{
  "date": "2026-04-23",
  "timezone": "America/New_York",
  "day_of_week": "Thursday",
  "iso_week": 17
}
```

### Next business day

> "I'm scheduling a task for July 3, 2025 in the US. What's the next business day after that?"

Tool call: `next_business_day(date="2025-07-03", country="US")`

```json
{
  "input_date": "2025-07-03",
  "next_business_day": "2025-07-07",
  "country": "US",
  "skipped_days": 4
}
```

### Previous business day

> "What was the last business day before July 4, 2025 in the US?"

Tool call: `previous_business_day(date="2025-07-04", country="US")`

```json
{
  "input_date": "2025-07-04",
  "previous_business_day": "2025-07-03",
  "country": "US",
  "skipped_days": 1
}
```

### Last business day of the month

> "When is the last business day of May 2026 in the US?"

Tool call: `last_business_day_of_month(year=2026, month=5, country="US")`

```json
{
  "year": 2026,
  "month": 5,
  "country": "US",
  "last_business_day": "2026-05-29",
  "last_calendar_day": "2026-05-31"
}
```

### Business days between two dates

> "How many business days are between December 20, 2025 and January 5, 2026 in the US?"

Tool call: `business_days_between(start_date="2025-12-20", end_date="2026-01-05", country="US")`

```json
{
  "start_date": "2025-12-20",
  "end_date": "2026-01-05",
  "country": "US",
  "inclusive": false,
  "business_days": 8,
  "calendar_days": 16,
  "holidays_in_range": [
    { "date": "2025-12-25", "name": "Christmas Day" },
    { "date": "2026-01-01", "name": "New Year's Day" }
  ]
}
```

### List holidays for a year (regional subdivision)

> "List the 2026 public holidays in Bavaria, Germany."

Tool call: `list_holidays(year=2026, country="DE", subdiv="BY")`

```json
{
  "year": 2026,
  "country": "DE",
  "holidays": [
    { "date": "2026-01-01", "name": "New Year's Day" },
    { "date": "2026-01-06", "name": "Epiphany" },
    { "date": "2026-04-03", "name": "Good Friday" },
    { "date": "2026-04-06", "name": "Easter Monday" },
    { "date": "2026-05-01", "name": "Labor Day" },
    { "date": "2026-05-14", "name": "Ascension Day" },
    { "date": "2026-05-25", "name": "Whit Monday" },
    { "date": "2026-06-04", "name": "Corpus Christi" },
    { "date": "2026-10-03", "name": "German Unity Day" },
    { "date": "2026-11-01", "name": "All Saints' Day" },
    { "date": "2026-12-25", "name": "Christmas Day" },
    { "date": "2026-12-26", "name": "Second Day of Christmas" }
  ],
  "subdiv": "BY"
}
```

### Discover supported subdivisions

> "Which German states (subdivisions) can I use for holiday lookups?"

Tool call: `get_supported_subdivisions(country="DE")`

```json
{
  "country": "DE",
  "subdivisions": ["BB","BE","BW","BY","HB","HE","HH","MV","NI","NW","RP","SH","SL","SN","ST","TH","Augsburg"],
  "aliases": {
    "Brandenburg": "BB",
    "Berlin": "BE",
    "Baden-Württemberg": "BW",
    "Bayern": "BY",
    "Bremen": "HB",
    "Hessen": "HE",
    "Hamburg": "HH",
    "Mecklenburg-Vorpommern": "MV",
    "Niedersachsen": "NI",
    "Nordrhein-Westfalen": "NW",
    "Rheinland-Pfalz": "RP",
    "Schleswig-Holstein": "SH",
    "Saarland": "SL",
    "Sachsen": "SN",
    "Sachsen-Anhalt": "ST",
    "Thüringen": "TH"
  }
}
```

- See `get_supported_countries()` for the full list of 250+ supported countries and their subdivision codes.

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
