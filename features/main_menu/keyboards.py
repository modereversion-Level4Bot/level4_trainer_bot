"""Keyboard builders for main menu feature."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from features.main_menu.context import MainMenuContext
from features.main_menu.texts import (
    exam_info_button_text,
    grammar_button_text,
    questions_button_text,
    settings_button_text,
)


MENU_GRAMMAR_CALLBACK = "menu:grammar"
MENU_QUESTIONS_CALLBACK = "menu:questions"
MENU_EXAM_INFO_CALLBACK = "exam_info:overview"
MENU_SETTINGS_CALLBACK = "menu:settings"


def build_main_menu_keyboard(language: str, *, context: MainMenuContext) -> InlineKeyboardMarkup:
    """Build localized main menu keyboard."""
    rows: list[list[InlineKeyboardButton]] = []
    top_row: list[InlineKeyboardButton] = []
    if context.has_grammar_content:
        top_row.append(
            InlineKeyboardButton(
                text=grammar_button_text(language),
                callback_data=MENU_GRAMMAR_CALLBACK,
            )
        )
    if context.has_questions_content:
        top_row.append(
            InlineKeyboardButton(
                text=questions_button_text(language),
                callback_data=MENU_QUESTIONS_CALLBACK,
            )
        )
    if top_row:
        rows.append(top_row)

    rows.append(
        [
            InlineKeyboardButton(
                text=exam_info_button_text(language),
                callback_data=MENU_EXAM_INFO_CALLBACK,
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text=settings_button_text(language),
                callback_data=MENU_SETTINGS_CALLBACK,
            )
        ]
    )

    return InlineKeyboardMarkup(rows)
