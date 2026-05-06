"""Compatibility facade for settings feature service API."""

from __future__ import annotations

from features.settings.callback_router import process_settings_callback
from features.settings.message_inputs import (
    process_settings_location,
    process_settings_text,
)
from features.settings.sections_service import (
    is_settings_waiting_for_custom_time,
    is_settings_waiting_for_location,
    show_settings_main,
)

__all__ = [
    "show_settings_main",
    "process_settings_callback",
    "process_settings_location",
    "process_settings_text",
    "is_settings_waiting_for_location",
    "is_settings_waiting_for_custom_time",
]
