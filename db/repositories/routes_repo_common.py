"""Common constants and validators for routes repositories."""

from __future__ import annotations


_COMPLETED_ROUTE_STATUSES = ("completed", "done", "passed", "finished")
_ALLOWED_STEP_TYPES = {"atis", "atc_command", "situation", "info"}


def _required_text(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"{field_name} is required")
    return normalized


def _optional_text(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _normalize_int(
    value: int,
    *,
    field_name: str,
    min_value: int | None = None,
) -> int:
    normalized = int(value)
    if min_value is not None and normalized < min_value:
        raise RuntimeError(f"{field_name} must be >= {min_value}")
    return normalized


def _normalize_positive_int(value: int, *, field_name: str) -> int:
    normalized = int(value)
    if normalized <= 0:
        raise RuntimeError(f"{field_name} must be positive integer")
    return normalized


def _normalize_is_active(value: int) -> int:
    normalized = int(value)
    if normalized not in {0, 1}:
        raise RuntimeError("is_active must be 0 or 1")
    return normalized


def _normalize_step_type(step_type: str) -> str:
    normalized = _required_text(step_type, field_name="step_type").lower()
    if normalized not in _ALLOWED_STEP_TYPES:
        allowed = ", ".join(sorted(_ALLOWED_STEP_TYPES))
        raise RuntimeError(f"step_type must be one of: {allowed}")
    return normalized
