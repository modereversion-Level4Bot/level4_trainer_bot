"""Validators for imported sheet rows."""

from __future__ import annotations


def media_requirements_consistent(required: int, path: str | None) -> bool:
    """
    Validate required/path consistency.

    Future rule:
    - required=1 and empty path -> invalid
    - required=0 and empty path -> valid
    """
    if int(required) == 1 and not (path or "").strip():
        return False
    return True
