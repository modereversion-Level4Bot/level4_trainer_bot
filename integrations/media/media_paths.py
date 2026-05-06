"""Static media path helpers."""

from __future__ import annotations

from pathlib import Path

from config import BASE_DIR


MEDIA_ROOT = BASE_DIR / "media"
AUDIO_DIR = MEDIA_ROOT / "audio"
VOICE_DIR = MEDIA_ROOT / "voice"
IMAGES_DIR = MEDIA_ROOT / "images"
