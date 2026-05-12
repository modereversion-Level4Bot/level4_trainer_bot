"""Project configuration loader."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _parse_admin_ids(raw_value: str) -> list[int]:
    if not raw_value.strip():
        return []

    parsed: list[int] = []
    for chunk in raw_value.split(","):
        value = chunk.strip()
        if not value:
            continue
        parsed.append(int(value))
    return parsed


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    admin_ids: list[int]
    app_env: str
    db_path: str
    bot_version: str
    google_sheet_id: str
    google_service_account_json_base64: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError(
            "BOT_TOKEN is missing. Fill it in .env file (see .env.example)."
        )

    admin_ids_raw = os.getenv("ADMIN_IDS", "")
    try:
        admin_ids = _parse_admin_ids(admin_ids_raw)
    except ValueError as exc:
        raise RuntimeError(
            "ADMIN_IDS must contain comma-separated integer Telegram IDs."
        ) from exc

    return Settings(
        bot_token=bot_token,
        admin_ids=admin_ids,
        app_env=os.getenv("APP_ENV", "local"),
        db_path=os.getenv("DB_PATH", "data/local/dev_main.db"),
        bot_version=os.getenv("BOT_VERSION", "0.1"),
        google_sheet_id=os.getenv("GOOGLE_SHEET_ID", "").strip(),
        google_service_account_json_base64=os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", ""
        ).strip(),
    )
