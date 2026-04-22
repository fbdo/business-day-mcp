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


def _get_country_holidays(country: str, years: int | list[int]) -> Any:
    try:
        return holidays.country_holidays(country.upper(), years=years)
    except NotImplementedError as e:
        raise ValueError(
            f"Unknown country code: {country}. Use get_supported_countries to see available codes."
        ) from e


def _is_weekend(d: datetime.date) -> bool:
    return d.weekday() >= 5


def _is_business_day(d: datetime.date, country_holidays: Any) -> bool:
    return not _is_weekend(d) and d not in country_holidays


def is_business_day(date: str, country: str) -> dict[str, Any]:
    """Check whether a date is a business day for a given country."""
    d = _parse_date(date)
    hols = _get_country_holidays(country, years=d.year)
    holiday_name = hols.get(d)
    return {
        "date": date,
        "country": country.upper(),
        "is_business_day": _is_business_day(d, hols),
        "is_weekend": _is_weekend(d),
        "is_holiday": holiday_name is not None,
        "holiday_name": holiday_name,
    }


mcp.tool(is_business_day)


def get_current_date(timezone: str = "UTC") -> dict[str, Any]:
    """Return the current date in the given IANA timezone."""
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
    date: str, country: str, inclusive: bool, step: int
) -> tuple[datetime.date, datetime.date, int]:
    """Advance `step` days at a time from `date` until a business day is found."""
    d = _parse_date(date)
    hols = _get_country_holidays(country, years=d.year)
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


def next_business_day(date: str, country: str, inclusive: bool = False) -> dict[str, Any]:
    """Return the next business day on/after (inclusive) or strictly after `date`."""
    d, candidate, skipped = _step_business_day(date, country, inclusive, step=1)
    return {
        "input_date": d.isoformat(),
        "next_business_day": candidate.isoformat(),
        "country": country.upper(),
        "skipped_days": skipped,
    }


def previous_business_day(date: str, country: str, inclusive: bool = False) -> dict[str, Any]:
    """Return the previous business day on/before (inclusive) or strictly before `date`."""
    d, candidate, skipped = _step_business_day(date, country, inclusive, step=-1)
    return {
        "input_date": d.isoformat(),
        "previous_business_day": candidate.isoformat(),
        "country": country.upper(),
        "skipped_days": skipped,
    }


def last_business_day_of_month(year: int, month: int, country: str) -> dict[str, Any]:
    """Return the last business day of a given month for a country."""
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {month}. Must be 1-12.")
    hols = _get_country_holidays(country, years=year)
    last_calendar_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
    d = last_calendar_day
    while not _is_business_day(d, hols):
        d -= datetime.timedelta(days=1)
    return {
        "year": year,
        "month": month,
        "country": country.upper(),
        "last_business_day": d.isoformat(),
        "last_calendar_day": last_calendar_day.isoformat(),
    }


def business_days_between(
    start_date: str, end_date: str, country: str, inclusive: bool = False
) -> dict[str, Any]:
    """Count business days and list weekday holidays between two dates."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        raise ValueError("start_date must be on or before end_date")
    span_years = end.year - start.year
    if span_years > _MAX_SPAN_YEARS:
        raise ValueError(
            f"Date range too large: {span_years} years exceeds max {_MAX_SPAN_YEARS} years."
        )
    hols = _get_country_holidays(country, years=list(range(start.year, end.year + 1)))
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
    return {
        "start_date": start_date,
        "end_date": end_date,
        "country": country.upper(),
        "inclusive": inclusive,
        "business_days": business_days,
        "calendar_days": (end - start).days + (1 if inclusive else 0),
        "holidays_in_range": holidays_in_range,
    }


def list_holidays(year: int, country: str) -> dict[str, Any]:
    """List all holidays for a given year and country, sorted by date."""
    hols = _get_country_holidays(country, years=year)
    return {
        "year": year,
        "country": country.upper(),
        "holidays": [{"date": d.isoformat(), "name": name} for d, name in sorted(hols.items())],
    }


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


def get_supported_countries() -> dict[str, Any]:
    """List all countries supported by the holidays library."""
    countries = sorted(
        (
            {"code": code, "name": _country_display_name(code)}
            for code in holidays.utils.list_supported_countries(include_aliases=False)
        ),
        key=lambda c: c["code"],
    )
    return {"countries": countries, "total": len(countries)}


mcp.tool(get_current_date)
mcp.tool(next_business_day)
mcp.tool(previous_business_day)
mcp.tool(last_business_day_of_month)
mcp.tool(business_days_between)
mcp.tool(list_holidays)
mcp.tool(get_supported_countries)


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()
