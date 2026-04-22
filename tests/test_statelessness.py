"""Principle #10: no caching — every call re-instantiates the holidays object."""

from __future__ import annotations

import business_day_mcp.server as srv


def test_country_holidays_invoked_each_call(monkeypatch):
    import holidays

    calls = {"n": 0}
    real = holidays.country_holidays

    def spy(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(holidays, "country_holidays", spy)
    srv.is_business_day(date="2026-04-21", country="DE")
    srv.is_business_day(date="2026-04-21", country="DE")
    assert calls["n"] >= 2
