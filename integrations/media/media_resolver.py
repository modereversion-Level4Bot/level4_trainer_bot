"""Resolve media files by relative DB paths."""

from __future__ import annotations

from pathlib import Path

from integrations.media.media_paths import MEDIA_ROOT


def resolve_media_path(relative_path: str | None) -> Path | None:
    """Resolve relative media path under media root."""
    if not relative_path:
        return None

    candidate = (MEDIA_ROOT / relative_path).resolve()
    media_root = MEDIA_ROOT.resolve()
    if media_root not in candidate.parents and candidate != media_root:
        return None
    return candidate
