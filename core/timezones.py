"""Timezone helpers for future onboarding flows."""

from __future__ import annotations

from timezonefinder import TimezoneFinder
import pytz


_timezone_finder = TimezoneFinder()


def detect_timezone_name(latitude: float, longitude: float) -> str | None:
    """Return timezone name by coordinates."""
    timezone_name = _timezone_finder.timezone_at(lat=latitude, lng=longitude)
    if timezone_name and timezone_name in pytz.all_timezones_set:
        return timezone_name
    return None


def is_timezone_valid(timezone_name: str) -> bool:
    """Validate timezone against pytz registry."""
    return timezone_name in pytz.all_timezones_set
