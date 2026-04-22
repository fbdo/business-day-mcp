# business-day-mcp

MCP server for business-day arithmetic with country-aware holiday calendars.

Answers questions like:
- Is today a business day in Germany?
- When is the last business day of April 2026?
- How many business days between Apr 21 and May 5 in the US?

Built on the [`holidays`](https://pypi.org/project/holidays/) library — supports 60+ countries out of the box.

## Install

```bash
uvx business-day-mcp
```

Or persistent install:

```bash
pip install business-day-mcp
```

## MCP Configuration

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
        "get_supported_countries"
      ]
    }
  }
}
```

All tools are read-only — safe to auto-approve.

## Conventions

- **Dates**: ISO 8601 strings (`YYYY-MM-DD`)
- **Countries**: ISO 3166-1 alpha-2 codes (`DE`, `US`, `GB`, ...)
- **Timezones**: IANA names (`Europe/Berlin`, `America/New_York`, ...)

## Development

```bash
git clone https://github.com/fbdo/business-day-mcp
cd business-day-mcp
uv sync --all-extras
uv run pytest
```

## License

MIT
