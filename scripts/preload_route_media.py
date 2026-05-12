"""Run route media preload pipeline for audio/images."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

_SUPPORTED_TYPES = ("audio", "image")
_TYPE_TO_SCRIPT = {
    "audio": PROJECT_ROOT / "scripts" / "preload_route_audio.py",
    "image": PROJECT_ROOT / "scripts" / "preload_route_images.py",
}


def _parse_types(value: str) -> list[str]:
    raw_items = [item.strip().lower() for item in (value or "").split(",")]
    normalized: list[str] = []
    for item in raw_items:
        if not item:
            continue
        if item not in _SUPPORTED_TYPES:
            raise argparse.ArgumentTypeError(
                f"Unsupported media type: {item}. Allowed: {', '.join(_SUPPORTED_TYPES)}."
            )
        if item not in normalized:
            normalized.append(item)
    if not normalized:
        raise argparse.ArgumentTypeError("At least one media type must be selected.")
    return normalized


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preload route media into Telegram file_id cache. "
            "Examples: --types image ; --types audio,image"
        )
    )
    parser.add_argument(
        "--types",
        type=_parse_types,
        default=["audio", "image"],
        help="Comma-separated list of media types to preload: audio,image",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    selected_types: list[str] = list(args.types)
    overall_exit_code = 0

    print(f"Selected media types: {', '.join(selected_types)}")
    for media_type in selected_types:
        script_path = _TYPE_TO_SCRIPT[media_type]
        command = [sys.executable, str(script_path)]
        print(f"Running {media_type} preload: {' '.join(command)}")
        completed = subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
        if completed.returncode != 0:
            overall_exit_code = completed.returncode
            print(f"{media_type} preload failed with exit code {completed.returncode}")
            break

    if overall_exit_code == 0:
        print("Route media preload completed.")
    return overall_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
