"""Google Sheets client helpers."""

from __future__ import annotations

import base64
import binascii
import json
import os
import re
from typing import Any

import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound
from google.oauth2.service_account import Credentials

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_URL_PATTERN = re.compile(r"/d/([a-zA-Z0-9-_]+)")


def get_google_sheet_id() -> str:
    """Read spreadsheet ID from environment."""
    raw_sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    if not raw_sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID is missing in .env")
    if raw_sheet_id.startswith("http"):
        match = SPREADSHEET_URL_PATTERN.search(raw_sheet_id)
        if not match:
            raise RuntimeError("GOOGLE_SHEET_ID is invalid. Use spreadsheet ID or full URL.")
        return match.group(1)
    return raw_sheet_id


def _decode_service_account_json(encoded: str) -> dict[str, Any]:
    """Decode base64 JSON credentials without exposing sensitive payload."""
    try:
        payload = base64.b64decode(encoded, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise RuntimeError("Could not decode service account JSON") from exc

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Service account JSON is invalid") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Service account JSON is invalid")
    return data


def build_client(*, service_account_json_base64: str | None = None) -> gspread.Client:
    """Build gspread client from base64 service account JSON."""
    encoded = (
        service_account_json_base64.strip()
        if service_account_json_base64 is not None
        else os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()
    )
    if not encoded:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 is missing in .env")

    data = _decode_service_account_json(encoded)
    credentials = Credentials.from_service_account_info(data, scopes=GOOGLE_SCOPES)
    return gspread.authorize(credentials)


def open_spreadsheet_by_id(
    client: gspread.Client,
    spreadsheet_id: str,
) -> gspread.Spreadsheet:
    """Open spreadsheet and return a friendly error on access issues."""
    try:
        return client.open_by_key(spreadsheet_id)
    except (SpreadsheetNotFound, APIError) as exc:
        raise RuntimeError(
            "Could not open spreadsheet. Check GOOGLE_SHEET_ID and sharing permissions."
        ) from exc
