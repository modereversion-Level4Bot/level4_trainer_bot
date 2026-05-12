"""Shared route-media path candidate builders for runtime and preload scripts."""

from __future__ import annotations

from pathlib import Path

from config import BASE_DIR


_MEDIA_ROOT = BASE_DIR / "media"
_ROUTES_MEDIA_ROOT = _MEDIA_ROOT / "routes"
_MEDIA_KIND_IMAGE = "image"
_MEDIA_KIND_AUDIO = "audio"


def _unique_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def build_route_media_candidates(media_file: str | None, *, media_kind: str) -> list[Path]:
    """Build candidate local paths for one route media reference."""
    normalized = (media_file or "").strip()
    if not normalized:
        return []

    if media_kind not in {_MEDIA_KIND_IMAGE, _MEDIA_KIND_AUDIO}:
        raise ValueError(f"Unsupported media kind: {media_kind}")

    raw_candidate = Path(normalized)
    if raw_candidate.is_absolute():
        return [raw_candidate]

    lower_parts = [part.lower() for part in raw_candidate.parts]
    is_media_prefixed = bool(lower_parts) and lower_parts[0] == "media"
    candidates: list[Path] = []

    if is_media_prefixed:
        # Explicit project-relative media path, e.g. media/routes/route_001/images/pic.jpg
        candidates.append(BASE_DIR / raw_candidate)
    else:
        # Primary standard: path in sheet is relative to media/routes/.
        # Example: route_001/images/pic.jpg -> media/routes/route_001/images/pic.jpg
        candidates.append(_ROUTES_MEDIA_ROOT / raw_candidate)

    if media_kind == _MEDIA_KIND_IMAGE:
        # Legacy flat folders for backward compatibility.
        if raw_candidate.parent == Path("."):
            candidates.append(_ROUTES_MEDIA_ROOT / "images" / raw_candidate.name)
            candidates.append(_MEDIA_ROOT / "images" / raw_candidate.name)
    else:
        # Legacy route-audio fallback for older flat layout.
        candidates.append(_ROUTES_MEDIA_ROOT / "audio" / raw_candidate)
        if raw_candidate.parent == Path("."):
            candidates.append(_MEDIA_ROOT / "audio" / raw_candidate.name)

    # Generic project-relative fallback for custom local layouts.
    candidates.append(BASE_DIR / raw_candidate)
    return _unique_paths(candidates)
