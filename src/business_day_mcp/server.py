"""business-day-mcp server."""

from __future__ import annotations

import calendar
import datetime
import zoneinfo
from typing import Any

import holidays
from fastmcp import FastMCP

mcp = FastMCP("business-day-mcp")

# DoS guards for date iteration (SR-F4).
_MAX_SPAN_YEARS = 100
_MAX_STEP_ITERATIONS = 3650  # ~10 years; far exceeds any real holiday gap.


def _parse_date(date_str: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid date format: {date_str}. Use ISO 8601 (YYYY-MM-DD).") from e


def _get_country_holidays(country: str, years: int | list[int], subdiv: str | None = None) -> Any:
    try:
        return holidays.country_holidays(country.upper(), subdiv=subdiv, years=years)
    except NotImplementedError as e:
        suffix = f" (subdiv={subdiv!r})" if subdiv is not None else ""
        raise ValueError(
            f"Unknown country code: {country!r}{suffix}. "
            "Use get_supported_countries to see available codes and subdivisions."
        ) from e


def _is_weekend(d: datetime.date) -> bool:
    return d.weekday() >= 5


def _is_business_day(d: datetime.date, country_holidays: Any) -> bool:
    return not _is_weekend(d) and d not in country_holidays


def is_business_day(date: str, country: str, subdiv: str | None = None) -> dict[str, Any]:
    """Check whether a date is a business day for a given country (optionally a subdivision).

    Use this when an agent needs to know if a specific calendar date is a working day —
    i.e. NOT a weekend and NOT a public holiday — under a country's official calendar.

    Args:
        date: ISO 8601 date string (YYYY-MM-DD), e.g. "2026-04-21".
        country: ISO 3166-1 alpha-2 country code. Case-insensitive (normalized to upper).
        subdiv: Optional country-specific subdivision code (state/province/region).
            Case-sensitive — pass it exactly as returned by get_supported_countries
            (e.g. "BY" for Bavaria, "CA" for California). When omitted, only
            nation-wide holidays are considered. Example: country="DE", subdiv="BY"
            treats Epiphany (Jan 6) as a holiday because it is observed only in Bavaria.
            Category filtering (e.g. catholic vs evangelical) is not currently supported.

    Returns:
        dict with keys: date, country, subdiv (only if provided), is_business_day,
        is_weekend, is_holiday, holiday_name (str or None).

    Raises:
        ValueError: if `date` is not valid ISO 8601, or `country`/`subdiv` is unknown.
    """
    d = _parse_date(date)
    hols = _get_country_holidays(country, years=d.year, subdiv=subdiv)
    holiday_name = hols.get(d)
    result: dict[str, Any] = {
        "date": date,
        "country": country.upper(),
        "is_business_day": _is_business_day(d, hols),
        "is_weekend": _is_weekend(d),
        "is_holiday": holiday_name is not None,
        "holiday_name": holiday_name,
    }
    if subdiv is not None:
        result["subdiv"] = subdiv
    return result


mcp.tool(is_business_day)


def get_current_date(timezone: str = "UTC") -> dict[str, Any]:
    """Return the current date in the given IANA timezone.

    Use this when an agent needs a stable, server-computed "today" — for example
    before calling other tools that require a concrete date. Does NOT consult any
    holiday calendar.

    Args:
        timezone: IANA timezone name (e.g. "UTC", "Europe/Berlin", "America/New_York",
            "Asia/Tokyo"). Defaults to "UTC".

    Returns:
        dict with keys: date (YYYY-MM-DD), timezone, day_of_week (full weekday name),
        iso_week (1-53).

    Raises:
        ValueError: if `timezone` is not a recognized IANA zone.
    """
    try:
        tz = zoneinfo.ZoneInfo(timezone)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError) as e:
        raise ValueError(
            f"Unknown timezone: {timezone}. Use IANA timezone names like "
            "'Europe/Berlin' or 'America/New_York'."
        ) from e
    now = datetime.datetime.now(tz=tz)
    return {
        "date": now.date().isoformat(),
        "timezone": timezone,
        "day_of_week": now.strftime("%A"),
        "iso_week": now.isocalendar().week,
    }


def _step_business_day(
    date: str, country: str, inclusive: bool, step: int, subdiv: str | None = None
) -> tuple[datetime.date, datetime.date, int]:
    """Advance `step` days at a time from `date` until a business day is found."""
    d = _parse_date(date)
    hols = _get_country_holidays(country, years=d.year, subdiv=subdiv)
    candidate = d if inclusive else d + datetime.timedelta(days=step)
    skipped = 0 if inclusive else 1
    iterations = 0
    while not _is_business_day(candidate, hols):
        candidate += datetime.timedelta(days=step)
        skipped += 1
        iterations += 1
        if iterations > _MAX_STEP_ITERATIONS:
            raise ValueError("Could not find a business day within 10 years of input.")
    return d, candidate, skipped


def next_business_day(
    date: str, country: str, inclusive: bool = False, subdiv: str | None = None
) -> dict[str, Any]:
    """Return the next business day on/after (inclusive) or strictly after `date`.

    Use this to move forward to the soonest working day — skipping weekends and
    public holidays.

    Args:
        date: ISO 8601 date string (YYYY-MM-DD) to start from.
        country: ISO 3166-1 alpha-2 code (case-insensitive, normalized to upper).
        inclusive: When True, `date` itself qualifies if it is a business day.
            When False (default), the search starts the day after `date`.
        subdiv: Optional country-specific subdivision code (case-sensitive; see
            get_supported_countries). When omitted, only nation-wide holidays are
            considered. Example: country="DE", subdiv="BY" will skip Epiphany
            (Jan 6) in Bavaria.

    Returns:
        dict with keys: input_date, next_business_day, country, subdiv (only if
        provided), skipped_days (number of non-business days traversed).

    Raises:
        ValueError: on invalid date, unknown country/subdiv, or if no business day
            is found within ~10 years.
    """
    d, candidate, skipped = _step_business_day(date, country, inclusive, step=1, subdiv=subdiv)
    result: dict[str, Any] = {
        "input_date": d.isoformat(),
        "next_business_day": candidate.isoformat(),
        "country": country.upper(),
        "skipped_days": skipped,
    }
    if subdiv is not None:
        result["subdiv"] = subdiv
    return result


def previous_business_day(
    date: str, country: str, inclusive: bool = False, subdiv: str | None = None
) -> dict[str, Any]:
    """Return the previous business day on/before (inclusive) or strictly before `date`.

    Use this to move backward to the most recent working day — skipping weekends
    and public holidays.

    Args:
        date: ISO 8601 date string (YYYY-MM-DD) to start from.
        country: ISO 3166-1 alpha-2 code (case-insensitive, normalized to upper).
        inclusive: When True, `date` itself qualifies if it is a business day.
            When False (default), the search starts the day before `date`.
        subdiv: Optional country-specific subdivision code (case-sensitive; see
            get_supported_countries). When omitted, only nation-wide holidays are
            considered.

    Returns:
        dict with keys: input_date, previous_business_day, country, subdiv (only if
        provided), skipped_days.

    Raises:
        ValueError: on invalid date, unknown country/subdiv, or if no business day
            is found within ~10 years.
    """
    d, candidate, skipped = _step_business_day(date, country, inclusive, step=-1, subdiv=subdiv)
    result: dict[str, Any] = {
        "input_date": d.isoformat(),
        "previous_business_day": candidate.isoformat(),
        "country": country.upper(),
        "skipped_days": skipped,
    }
    if subdiv is not None:
        result["subdiv"] = subdiv
    return result


def last_business_day_of_month(
    year: int, month: int, country: str, subdiv: str | None = None
) -> dict[str, Any]:
    """Return the last business day of a given month for a country.

    Use this for end-of-month billing, reporting, or settlement dates that must
    land on a working day. Walks backward from the last calendar day, skipping
    weekends and holidays.

    Args:
        year: Four-digit year (e.g. 2026).
        month: Month 1-12.
        country: ISO 3166-1 alpha-2 code (case-insensitive, normalized to upper).
        subdiv: Optional country-specific subdivision code (case-sensitive; see
            get_supported_countries). When omitted, only nation-wide holidays are
            considered.

    Returns:
        dict with keys: year, month, country, subdiv (only if provided),
        last_business_day (YYYY-MM-DD), last_calendar_day (YYYY-MM-DD).

    Raises:
        ValueError: on invalid month, unknown country/subdiv.
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {month}. Must be 1-12.")
    hols = _get_country_holidays(country, years=year, subdiv=subdiv)
    last_calendar_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
    d = last_calendar_day
    while not _is_business_day(d, hols):
        d -= datetime.timedelta(days=1)
    result: dict[str, Any] = {
        "year": year,
        "month": month,
        "country": country.upper(),
        "last_business_day": d.isoformat(),
        "last_calendar_day": last_calendar_day.isoformat(),
    }
    if subdiv is not None:
        result["subdiv"] = subdiv
    return result


def business_days_between(
    start_date: str,
    end_date: str,
    country: str,
    inclusive: bool = False,
    subdiv: str | None = None,
) -> dict[str, Any]:
    """Count business days and list weekday holidays between two dates.

    Use this to measure working-day spans for SLAs, delivery windows, or payroll
    periods. Weekend holidays are NOT listed in `holidays_in_range` (they do not
    reduce the business-day count); weekday holidays are.

    Args:
        start_date: ISO 8601 date string (YYYY-MM-DD). Must be <= end_date.
        end_date: ISO 8601 date string (YYYY-MM-DD).
        country: ISO 3166-1 alpha-2 code (case-insensitive, normalized to upper).
        inclusive: When True, both endpoints count toward the range. When False
            (default), end_date is excluded (half-open interval).
        subdiv: Optional country-specific subdivision code (case-sensitive; see
            get_supported_countries). When omitted, only nation-wide holidays are
            considered.

    Returns:
        dict with keys: start_date, end_date, country, subdiv (only if provided),
        inclusive, business_days (int), calendar_days (int), holidays_in_range
        (list of {date, name} for weekday holidays only).

    Raises:
        ValueError: if `start_date > end_date`, the span exceeds 100 years,
            dates are malformed, or country/subdiv is unknown.
    """
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        raise ValueError("start_date must be on or before end_date")
    span_years = end.year - start.year
    if span_years > _MAX_SPAN_YEARS:
        raise ValueError(
            f"Date range too large: {span_years} years exceeds max {_MAX_SPAN_YEARS} years."
        )
    hols = _get_country_holidays(
        country, years=list(range(start.year, end.year + 1)), subdiv=subdiv
    )
    last = end if inclusive else end - datetime.timedelta(days=1)
    business_days = 0
    holidays_in_range: list[dict[str, str]] = []
    d = start
    while d <= last:
        if _is_business_day(d, hols):
            business_days += 1
        if d in hols and not _is_weekend(d):
            holidays_in_range.append({"date": d.isoformat(), "name": hols[d]})
        d += datetime.timedelta(days=1)
    result: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
        "country": country.upper(),
        "inclusive": inclusive,
        "business_days": business_days,
        "calendar_days": (end - start).days + (1 if inclusive else 0),
        "holidays_in_range": holidays_in_range,
    }
    if subdiv is not None:
        result["subdiv"] = subdiv
    return result


def list_holidays(year: int, country: str, subdiv: str | None = None) -> dict[str, Any]:
    """List all holidays for a given year and country, sorted by date.

    Use this to enumerate the full holiday calendar — for display, planning, or
    cross-referencing. Includes holidays that fall on weekends.

    Args:
        year: Four-digit year (e.g. 2026).
        country: ISO 3166-1 alpha-2 code (case-insensitive, normalized to upper).
        subdiv: Optional country-specific subdivision code (case-sensitive; see
            get_supported_countries). When omitted, only nation-wide holidays are
            returned. Example: country="DE", subdiv="BY" adds Bavarian regional
            holidays such as Epiphany (Jan 6) and All Saints' Day (Nov 1).
            Category filtering (e.g. catholic vs evangelical) is not currently
            supported; the union of applicable categories is returned.

    Returns:
        dict with keys: year, country, subdiv (only if provided), holidays
        (list of {date: YYYY-MM-DD, name: str}, sorted ascending by date).

    Raises:
        ValueError: on unknown country/subdiv.
    """
    hols = _get_country_holidays(country, years=year, subdiv=subdiv)
    result: dict[str, Any] = {
        "year": year,
        "country": country.upper(),
        "holidays": [{"date": d.isoformat(), "name": name} for d, name in sorted(hols.items())],
    }
    if subdiv is not None:
        result["subdiv"] = subdiv
    return result


def _country_display_name(code: str) -> str:
    cls = getattr(holidays, code, None)
    if cls is None:
        return code
    name = getattr(cls, "country_name", None)
    if name:
        return str(name)
    doc = getattr(cls, "__doc__", None)
    if doc:
        return str(doc).strip().split("\n")[0]
    return code


def _country_subdivisions(code: str) -> list[str]:
    """Return subdivision codes for a country, or [] on failure / no subdivisions."""
    try:
        subs = holidays.country_holidays(code).subdivisions
    except Exception:  # never crash the catalog tool on a single-country failure
        return []
    return list(subs) if subs else []


def get_supported_countries() -> dict[str, Any]:
    """List all countries supported by the holidays library, with subdivisions.

    Use this as the discovery tool before calling any country-aware tool. It tells
    the agent which ISO country codes are valid AND which subdivision codes may be
    passed as the optional `subdiv` argument on other tools.

    IMPORTANT: Subdivision codes are case-sensitive — use them verbatim as returned
    here. Country codes are case-insensitive.

    Returns:
        dict with keys:
          - countries: list of {code: 2-letter ISO code, name: str,
              subdivisions: list[str]}, sorted by code. `subdivisions` is [] for
              countries without regional variants (e.g. JP), and may also be []
              if the library raised an error while introspecting that country.
          - total: number of countries returned.
    """
    countries: list[dict[str, Any]] = sorted(
        (
            {
                "code": code,
                "name": _country_display_name(code),
                "subdivisions": _country_subdivisions(code),
            }
            for code in holidays.utils.list_supported_countries(include_aliases=False)
        ),
        key=lambda c: str(c["code"]),
    )
    return {"countries": countries, "total": len(countries)}


def get_supported_subdivisions(country: str) -> dict[str, Any]:
    """List subdivision codes and aliases for a country's holiday calendar.

    Use this to discover valid `subdiv` values before calling any country-aware
    holiday tool (e.g. `is_business_day`, `list_holidays`, `next_business_day`).

    IMPORTANT: Subdivision codes are case-sensitive and must be passed through
    `subdiv` exactly as returned here — either a canonical code from
    `subdivisions` or an alias key from `aliases`. Do NOT upper-case or otherwise
    normalize them.

    Example: `country="DE"` returns `"BY"` among its subdivisions. Passing
    `subdiv="BY"` to `list_holidays(year=2026, country="DE", subdiv="BY")` then
    reveals Bavarian regional holidays such as Epiphany (Jan 6).

    Args:
        country: ISO 3166-1 alpha-2 code (case-insensitive, normalized to upper).

    Returns:
        dict with keys:
          - country: normalized uppercase code.
          - subdivisions: list of canonical subdivision codes (empty if the
              country has no regional variants, e.g. JP).
          - aliases: dict mapping alias (mixed-case, verbatim) → canonical code
              (empty dict if the country exposes no aliases).

    Raises:
        ValueError: if `country` is unknown/unsupported.
    """
    code = country.upper()
    try:
        hols = holidays.country_holidays(code)
    except NotImplementedError as e:
        raise ValueError(
            f"Unknown country code: {country!r}. "
            "Use get_supported_countries to see available codes and subdivisions."
        ) from e
    subs = hols.subdivisions
    aliases = hols.subdivisions_aliases
    return {
        "country": code,
        "subdivisions": list(subs) if subs else [],
        "aliases": dict(aliases) if aliases else {},
    }


mcp.tool(get_current_date)
mcp.tool(next_business_day)
mcp.tool(previous_business_day)
mcp.tool(last_business_day_of_month)
mcp.tool(business_days_between)
mcp.tool(list_holidays)
mcp.tool(get_supported_countries)
mcp.tool(get_supported_subdivisions)


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()
