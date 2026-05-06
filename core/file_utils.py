"""File utilities used by media preload/runtime helpers."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path


SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".m4a"}


def _to_path(path: str | Path) -> Path:
    if isinstance(path, Path):
        return path
    return Path(path)


def calculate_file_checksum(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Calculate SHA256 checksum without loading whole file into memory."""
    file_path = _to_path(path)
    digest = sha256()
    with file_path.open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def get_file_size(path: str | Path) -> int:
    """Return file size in bytes."""
    file_path = _to_path(path)
    return int(file_path.stat().st_size)


def is_supported_audio_extension(path: str | Path) -> bool:
    """Return True when file extension is one of supported audio formats."""
    file_path = _to_path(path)
    return file_path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
