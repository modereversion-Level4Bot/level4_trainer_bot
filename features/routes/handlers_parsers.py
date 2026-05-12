"""Pure callback payload parsers for routes handlers."""

from __future__ import annotations

from features.routes.keyboards import CB_ROUTES_OPEN_PREFIX


def _parse_int_payload(callback_data: str, prefix: str) -> int | None:
    if not callback_data.startswith(prefix):
        return None
    raw_payload = callback_data[len(prefix) :].strip()
    if not raw_payload:
        return None
    try:
        normalized = int(raw_payload)
    except ValueError:
        return None
    if normalized <= 0:
        return None
    return normalized


def _parse_route_open_payload(callback_data: str) -> tuple[int, int] | None:
    if not callback_data.startswith(CB_ROUTES_OPEN_PREFIX):
        return None
    raw_payload = callback_data[len(CB_ROUTES_OPEN_PREFIX) :].strip()
    if not raw_payload:
        return None
    parts = raw_payload.split(":")
    if len(parts) != 2:
        return None
    try:
        route_id = int(parts[0])
        page = int(parts[1])
    except ValueError:
        return None
    if route_id <= 0 or page <= 0:
        return None
    return route_id, page


def _parse_route_step_payload(callback_data: str, prefix: str) -> tuple[int, int] | None:
    if not callback_data.startswith(prefix):
        return None
    raw_payload = callback_data[len(prefix) :].strip()
    if not raw_payload:
        return None
    parts = raw_payload.split(":")
    if len(parts) != 2:
        return None
    try:
        route_id = int(parts[0])
        step_number = int(parts[1])
    except ValueError:
        return None
    if route_id <= 0 or step_number <= 0:
        return None
    return route_id, step_number


def _parse_route_page_payload(callback_data: str, prefix: str) -> tuple[int, int] | None:
    if not callback_data.startswith(prefix):
        return None
    raw_payload = callback_data[len(prefix) :].strip()
    if not raw_payload:
        return None
    parts = raw_payload.split(":")
    if len(parts) != 2:
        return None
    try:
        route_id = int(parts[0])
        page = int(parts[1])
    except ValueError:
        return None
    if route_id <= 0 or page <= 0:
        return None
    return route_id, page


def _parse_route_item_page_payload(
    callback_data: str,
    prefix: str,
) -> tuple[int, int, int] | None:
    if not callback_data.startswith(prefix):
        return None
    raw_payload = callback_data[len(prefix) :].strip()
    if not raw_payload:
        return None
    parts = raw_payload.split(":")
    if len(parts) != 3:
        return None
    try:
        route_id = int(parts[0])
        item_id = int(parts[1])
        page = int(parts[2])
    except ValueError:
        return None
    if route_id <= 0 or item_id <= 0 or page <= 0:
        return None
    return route_id, item_id, page
