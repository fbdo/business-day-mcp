"""business-day-mcp server."""

from __future__ import annotations

import datetime
from typing import Any

import holidays
from fastmcp import FastMCP

mcp: FastMCP = FastMCP("business-day-mcp")


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


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()
