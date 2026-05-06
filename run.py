"""Entry point for Level4Trainer Telegram bot."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.application import create_application
from config import get_settings
from core.logging import setup_logging
from db.init_db import init_db
from telegram.error import InvalidToken, TelegramError


logger = logging.getLogger(__name__)


def main() -> None:
    """Initialize project pieces and start polling."""
    settings = get_settings()
    setup_logging(settings.app_env)
    init_db()

    application = create_application(settings)
    try:
        application.run_polling(drop_pending_updates=False)
    except InvalidToken:
        logger.error("BOT_TOKEN rejected by Telegram API. Check BOT_TOKEN in .env.")
        raise SystemExit(1)
    except TelegramError as exc:
        logger.error("Telegram API startup error: %s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
