"""Keyboard builders for questions feature."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from features.questions.texts import (
    back_button_text,
    back_to_question_button_text,
    continue_button_text,
    finish_button_text,
    go_to_level5_button_text,
    level_button_text,
    levels_button_text,
    main_menu_button_text,
    next_button_text,
    previous_button_text,
    question_review_button_text,
    repeat_level_button_text,
    start_over_button_text,
    take_again_button_text,
)


QUESTIONS_CALLBACK_PREFIX = "questions:"

CB_QUESTIONS_LEVELS = "questions:levels"
CB_QUESTIONS_HOME = "questions:home"

CB_QUESTIONS_LEVEL_PREFIX = "questions:level:"
CB_QUESTIONS_CONTINUE_PREFIX = "questions:continue:"
CB_QUESTIONS_START_PREFIX = "questions:start:"
CB_QUESTIONS_VIEW_PREFIX = "questions:view:"
CB_QUESTIONS_PREV_PREFIX = "questions:prev:"
CB_QUESTIONS_NEXT_PREFIX = "questions:next:"
CB_QUESTIONS_FINISH_PREFIX = "questions:finish:"
CB_QUESTIONS_REPEAT_PREFIX = "questions:repeat:"
CB_QUESTIONS_GO_LEVEL_PREFIX = "questions:go_level:"

VIEW_BASE = "base"
VIEW_REVIEW = "review"


def cb_level(level: int) -> str:
    return f"{CB_QUESTIONS_LEVEL_PREFIX}{int(level)}"


def cb_continue(level: int) -> str:
    return f"{CB_QUESTIONS_CONTINUE_PREFIX}{int(level)}"


def cb_start_over(level: int) -> str:
    return f"{CB_QUESTIONS_START_PREFIX}{int(level)}"


def cb_view(level: int, question_number: int, view_mode: str) -> str:
    return f"{CB_QUESTIONS_VIEW_PREFIX}{int(level)}:{int(question_number)}:{view_mode}"


def cb_prev(level: int, question_number: int) -> str:
    return f"{CB_QUESTIONS_PREV_PREFIX}{int(level)}:{int(question_number)}"


def cb_next(level: int, question_number: int) -> str:
    return f"{CB_QUESTIONS_NEXT_PREFIX}{int(level)}:{int(question_number)}"


def cb_finish(level: int, question_number: int) -> str:
    return f"{CB_QUESTIONS_FINISH_PREFIX}{int(level)}:{int(question_number)}"


def cb_repeat(level: int) -> str:
    return f"{CB_QUESTIONS_REPEAT_PREFIX}{int(level)}"


def cb_go_level(level: int) -> str:
    return f"{CB_QUESTIONS_GO_LEVEL_PREFIX}{int(level)}"


def _navigation_rows(
    language: str,
    *,
    level: int,
    question_number: int,
    has_prev: bool,
    has_next: bool,
) -> list[list[InlineKeyboardButton]]:
    if has_prev and has_next:
        return [
            [
                InlineKeyboardButton(
                    text=previous_button_text(language),
                    callback_data=cb_prev(level, question_number),
                ),
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_QUESTIONS_HOME,
                ),
                InlineKeyboardButton(
                    text=next_button_text(language),
                    callback_data=cb_next(level, question_number),
                ),
            ]
        ]
    if has_prev and not has_next:
        return [
            [
                InlineKeyboardButton(
                    text=previous_button_text(language),
                    callback_data=cb_prev(level, question_number),
                ),
                InlineKeyboardButton(
                    text=finish_button_text(language),
                    callback_data=cb_finish(level, question_number),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_QUESTIONS_HOME,
                )
            ],
        ]
    if has_next:
        return [
            [
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_QUESTIONS_HOME,
                ),
                InlineKeyboardButton(
                    text=next_button_text(language),
                    callback_data=cb_next(level, question_number),
                ),
            ]
        ]
    return [
        [
            InlineKeyboardButton(
                text=finish_button_text(language),
                callback_data=cb_finish(level, question_number),
            )
        ],
        [
            InlineKeyboardButton(
                text=main_menu_button_text(language),
                callback_data=CB_QUESTIONS_HOME,
            )
        ],
    ]


def build_levels_keyboard(
    language: str,
    *,
    has_level4: bool,
    has_level5: bool,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if has_level4:
        rows.append(
            [
                InlineKeyboardButton(
                    text=level_button_text(4),
                    callback_data=cb_level(4),
                )
            ]
        )
    if has_level5:
        rows.append(
            [
                InlineKeyboardButton(
                    text=level_button_text(5),
                    callback_data=cb_level(5),
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=main_menu_button_text(language),
                callback_data=CB_QUESTIONS_HOME,
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_empty_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_QUESTIONS_HOME,
                )
            ]
        ]
    )


def build_continue_start_over_keyboard(language: str, *, level: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=start_over_button_text(language),
                    callback_data=cb_start_over(level),
                ),
                InlineKeyboardButton(
                    text=continue_button_text(language),
                    callback_data=cb_continue(level),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=back_button_text(language),
                    callback_data=CB_QUESTIONS_LEVELS,
                ),
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_QUESTIONS_HOME,
                ),
            ],
        ]
    )


def build_completed_reentry_keyboard(language: str, *, level: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=back_button_text(language),
                    callback_data=CB_QUESTIONS_LEVELS,
                ),
                InlineKeyboardButton(
                    text=take_again_button_text(language),
                    callback_data=cb_start_over(level),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_QUESTIONS_HOME,
                )
            ],
        ]
    )


def build_base_question_keyboard(
    language: str,
    *,
    level: int,
    question_number: int,
    has_review_content: bool,
    has_prev: bool,
    has_next: bool,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if has_review_content:
        rows.append(
            [
                InlineKeyboardButton(
                    text=question_review_button_text(language),
                    callback_data=cb_view(level, question_number, VIEW_REVIEW),
                )
            ]
        )

    rows.extend(
        _navigation_rows(
            language,
            level=level,
            question_number=question_number,
            has_prev=has_prev,
            has_next=has_next,
        )
    )
    return InlineKeyboardMarkup(rows)


def build_review_keyboard(
    language: str,
    *,
    level: int,
    question_number: int,
    has_prev: bool,
    has_next: bool,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=back_to_question_button_text(language),
                callback_data=cb_view(level, question_number, VIEW_BASE),
            )
        ]
    ]

    rows.extend(
        _navigation_rows(
            language,
            level=level,
            question_number=question_number,
            has_prev=has_prev,
            has_next=has_next,
        )
    )
    return InlineKeyboardMarkup(rows)


def build_level4_completion_keyboard(language: str, *, has_level5: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if has_level5:
        rows.append(
            [
                InlineKeyboardButton(
                    text=go_to_level5_button_text(language),
                    callback_data=cb_go_level(5),
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=repeat_level_button_text(language, 4),
                callback_data=cb_repeat(4),
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=levels_button_text(language),
                callback_data=CB_QUESTIONS_LEVELS,
            ),
            InlineKeyboardButton(
                text=main_menu_button_text(language),
                callback_data=CB_QUESTIONS_HOME,
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_level5_completion_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=repeat_level_button_text(language, 5),
                    callback_data=cb_repeat(5),
                )
            ],
            [
                InlineKeyboardButton(
                    text=levels_button_text(language),
                    callback_data=CB_QUESTIONS_LEVELS,
                ),
                InlineKeyboardButton(
                    text=main_menu_button_text(language),
                    callback_data=CB_QUESTIONS_HOME,
                ),
            ],
        ]
    )
