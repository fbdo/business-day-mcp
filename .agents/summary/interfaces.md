# Interfaces

<!-- metadata: scope=interfaces, audience=ai-assistants, topic=tool-contracts -->

Public surface = the eight MCP tools exposed by `business_day_mcp.server`. Each tool is called over MCP JSON-RPC (`tools/call`) with the parameter names and types documented below. All tools are read-only and return a JSON-serializable `dict`.

Common conventions (enforced in code):

- Dates: ISO 8601 `YYYY-MM-DD`.
- Country: ISO 3166-1 alpha-2, case-insensitive on input, normalized to upper-case in responses.
- Timezone: IANA name.
- Errors: `ValueError` with a human-readable message.

---

## `is_business_day(date, country) -> dict`

Check whether a single date is a business day for a country.

**Parameters**

| Name | Type | Required | Notes |
|------|------|----------|-------|
| `date` | str | yes | ISO 8601 |
| `country` | str | yes | ISO 3166-1 alpha-2 |

**Returns**

```json
{
  "date": "2026-04-21",
  "country": "DE",
  "is_business_day": true,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

`holiday_name` is `null` when the date is not a holiday; otherwise the localized name from the `holidays` library.

**Errors**: invalid date format; unknown country.

---

## `get_current_date(timezone="UTC") -> dict`

Current date in a given IANA timezone. Uses the process clock.

**Parameters**

| Name | Type | Required | Default | Notes |
|------|------|----------|---------|-------|
| `timezone` | str | no | `"UTC"` | IANA name |

**Returns**

```json
{
  "date": "2026-04-22",
  "timezone": "Europe/Berlin",
  "day_of_week": "Wednesday",
  "iso_week": 17
}
```

**Errors**: unknown timezone.

---

## `next_business_day(date, country, inclusive=False) -> dict`

First business day on/after `date`.

**Parameters**

| Name | Type | Required | Default | Notes |
|------|------|----------|---------|-------|
| `date` | str | yes | — | ISO 8601 |
| `country` | str | yes | — | alpha-2 |
| `inclusive` | bool | no | `False` | If `True` and `date` is a business day, return it. |

**Returns**

```json
{
  "input_date": "2026-04-03",
  "next_business_day": "2026-04-07",
  "country": "DE",
  "skipped_days": 4
}
```

`skipped_days` counts every day stepped over (weekends + holidays). Zero only when `inclusive=True` and the input is already a business day.

**Errors**: invalid date; unknown country; could not find a business day within 10 years (safety cap).

---

## `previous_business_day(date, country, inclusive=False) -> dict`

First business day on/before `date`. Same shape as `next_business_day` but the key is `previous_business_day`.

**Returns**

```json
{
  "input_date": "2026-04-06",
  "previous_business_day": "2026-04-02",
  "country": "DE",
  "skipped_days": 4
}
```

---

## `last_business_day_of_month(year, month, country) -> dict`

Walks backward from the last calendar day of the given month.

**Parameters**

| Name | Type | Required | Notes |
|------|------|----------|-------|
| `year` | int | yes | |
| `month` | int | yes | `1`–`12`; other values raise `ValueError` |
| `country` | str | yes | alpha-2 |

**Returns**

```json
{
  "year": 2026,
  "month": 4,
  "country": "DE",
  "last_business_day": "2026-04-30",
  "last_calendar_day": "2026-04-30"
}
```

---

## `business_days_between(start_date, end_date, country, inclusive=False) -> dict`

Counts business days and collects weekday holidays in a range.

**Parameters**

| Name | Type | Required | Default | Notes |
|------|------|----------|---------|-------|
| `start_date` | str | yes | — | |
| `end_date` | str | yes | — | Must be `>= start_date` |
| `country` | str | yes | — | |
| `inclusive` | bool | no | `False` | Include `end_date` in the iteration. |

**Returns**

```json
{
  "start_date": "2026-04-21",
  "end_date": "2026-05-05",
  "country": "US",
  "inclusive": false,
  "business_days": 10,
  "calendar_days": 14,
  "holidays_in_range": [
    {"date": "2026-05-04", "name": "Some holiday"}
  ]
}
```

`holidays_in_range` contains only holidays that fall on a weekday (Mon–Fri); weekend holidays are suppressed because they don't reduce the business-day count.

`calendar_days` is `(end - start).days + (1 if inclusive else 0)`.

**Errors**:

- Invalid date format.
- `start_date > end_date` → `ValueError("start_date must be on or before end_date")`.
- Span wider than `_MAX_SPAN_YEARS` (100) → `ValueError`.
- Unknown country.

---

## `list_holidays(year, country) -> dict`

All holidays for a year+country, sorted by date.

**Parameters**

| Name | Type | Required |
|------|------|----------|
| `year` | int | yes |
| `country` | str | yes |

**Returns**

```json
{
  "year": 2026,
  "country": "DE",
  "holidays": [
    {"date": "2026-01-01", "name": "Neujahr"},
    {"date": "2026-04-03", "name": "Karfreitag"}
  ]
}
```

Holiday names come from the `holidays` library and are locale-specific (German for DE, English for US, etc.).

---

## `get_supported_countries() -> dict`

Enumerates every country code the underlying `holidays` library supports. Aliases excluded (`include_aliases=False`).

**Returns**

```json
{
  "countries": [
    {"code": "AE", "name": "United Arab Emirates"},
    {"code": "AR", "name": "Argentina"}
  ],
  "total": 142
}
```

`total` reflects the runtime count from `holidays.utils.list_supported_countries` — it changes when the `holidays` dependency is upgraded. Tests assert `total >= 50` and include at least US, DE, GB, FR, JP, CA, AU, BR (see `tests/test_metadata.py`).

---

## Error Model Summary

| Cause | Tools affected | Exception |
|-------|----------------|-----------|
| Bad date string | every tool taking `date`/`start_date`/`end_date` | `ValueError` |
| Unknown country | every tool taking `country` | `ValueError` |
| Unknown timezone | `get_current_date` | `ValueError` |
| Invalid month (`<1` or `>12`) | `last_business_day_of_month` | `ValueError` |
| `start_date > end_date` | `business_days_between` | `ValueError` |
| Range > 100 years | `business_days_between` | `ValueError` |
| Step loop > 10 years | `next_business_day`, `previous_business_day` | `ValueError` |

FastMCP surfaces these as MCP tool errors to the client.
