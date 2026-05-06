"""Keyboard builders for exam info feature."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from features.exam_info.texts import (
    back_button_text,
    interview_button_text,
    main_menu_button_text,
    post_flight_button_text,
    role_play_button_text,
)


EXAM_INFO_CALLBACK_PREFIX = "exam_info:"
CB_EXAM_INFO_OVERVIEW = "exam_info:overview"
CB_EXAM_INFO_INTERVIEW = "exam_info:interview"
CB_EXAM_INFO_ROLE_PLAY = "exam_info:role_play"
CB_EXAM_INFO_POST_FLIGHT = "exam_info:post_flight"
CB_EXAM_INFO_MAIN_MENU = "exam_info:main_menu"


def build_exam_info_overview_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=interview_button_text(language),
                    callback_data=CB_EXAM_INFO_INTERVIEW,
                )
            ],
            [
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_EXAM_INFO_MAIN_MENU,
                )
            ],
        ]
    )


def build_exam_info_interview_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=role_play_button_text(language),
                    callback_data=CB_EXAM_INFO_ROLE_PLAY,
                )
            ],
            [
                InlineKeyboardButton(
                    text=back_button_text(language),
                    callback_data=CB_EXAM_INFO_OVERVIEW,
                ),
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_EXAM_INFO_MAIN_MENU,
                ),
            ],
        ]
    )


def build_exam_info_role_play_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=post_flight_button_text(language),
                    callback_data=CB_EXAM_INFO_POST_FLIGHT,
                )
            ],
            [
                InlineKeyboardButton(
                    text=back_button_text(language),
                    callback_data=CB_EXAM_INFO_INTERVIEW,
                ),
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_EXAM_INFO_MAIN_MENU,
                ),
            ],
        ]
    )


def build_exam_info_post_flight_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_EXAM_INFO_MAIN_MENU,
                )
            ],
        ]
    )
