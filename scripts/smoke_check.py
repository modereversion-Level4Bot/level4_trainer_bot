"""Quick local smoke check for project skeleton."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.application import create_application
from config import get_settings
from db.init_db import init_db


def main() -> None:
    init_db()
    print("OK: DB schema initialized.")

    try:
        settings = get_settings()
    except RuntimeError as exc:
        print(f"WARN: BOT_TOKEN missing, application build skipped. ({exc})")
        return

    application = create_application(settings)
    handlers_count = len(application.handlers)
    print(f"OK: Application built. Handler groups count: {handlers_count}")


if __name__ == "__main__":
    main()
