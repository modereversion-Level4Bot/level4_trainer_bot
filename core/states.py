"""Conversation state placeholders."""

from __future__ import annotations

from enum import IntEnum


class OnboardingState(IntEnum):
    """Reserved onboarding states."""

    PICK_LANGUAGE = 1
    PICK_TIMEZONE = 2
    COMPLETE = 3

