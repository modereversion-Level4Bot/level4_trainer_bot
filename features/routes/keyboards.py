"""Keyboard builders for routes feature."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from features.routes.texts import (
    normalize_language,
    route_another_route_button_text,
    route_hide_answer_button_text,
    route_hide_atis_button_text,
    route_hide_command_button_text,
    route_hide_hint_button_text,
    route_interrupt_stay_button,
    route_interrupt_yes_button,
    route_news_item_button_text,
    route_news_hide_transcript_button_text,
    route_news_show_transcript_button_text,
    route_question_block_button_text,
    route_question_finish_button_text,
    route_question_translate_button_text,
    route_to_blocks_button_text,
    route_to_news_list_button_text,
    route_to_route_button_text,
    route_show_answer_button_text,
    route_show_atis_button_text,
    route_show_command_button_text,
    route_show_hint_button_text,
)


ROUTES_CALLBACK_PREFIX = "routes:"
CB_ROUTES_LIST_PREFIX = "routes:list:"
CB_ROUTES_OPEN_PREFIX = "routes:open:"
CB_ROUTES_START_PREFIX = "routes:start:"
CB_ROUTES_NEWS_PREFIX = "routes:news:"
CB_ROUTES_QUESTIONS_PREFIX = "routes:questions:"
CB_ROUTES_BACK_LIST_PREFIX = "routes:back_list:"
CB_ROUTES_HOME = "routes:home"
CB_ROUTES_NEWS_LIST_PREFIX = "routes:news:list:"
CB_ROUTES_NEWS_OPEN_PREFIX = "routes:news:open:"
CB_ROUTES_QB_LIST_PREFIX = "routes:qb:list:"
CB_ROUTES_QB_OPEN_PREFIX = "routes:qb:open:"
CB_ROUTES_STEP_NEXT_PREFIX = "routes:step:next:"
CB_ROUTES_STEP_BACK_PREFIX = "routes:step:back:"
CB_ROUTES_STEP_TR_PREFIX = "routes:step:tr:"
CB_ROUTES_STEP_ANS_PREFIX = "routes:step:ans:"
CB_ROUTES_INTERRUPT_ASK_PREFIX = "routes:int:ask:"
CB_ROUTES_INTERRUPT_YES_PREFIX = "routes:int:yes:"
CB_ROUTES_INTERRUPT_NO_PREFIX = "routes:int:no:"
CB_ROUTES_NEWS_TR_PREFIX = "routes:news:tr:"
CB_ROUTES_NEWS_Q_PREFIX = "routes:news:q:"
CB_ROUTES_Q_NEXT_PREFIX = "routes:q:next:"
CB_ROUTES_Q_BACK_PREFIX = "routes:q:back:"
CB_ROUTES_Q_RU_PREFIX = "routes:q:ru:"
CB_ROUTES_Q_FINISH_PREFIX = "routes:q:finish:"
CB_ROUTES_ANOTHER = "routes:another"
CB_ROUTES_TO_ROUTE_PREFIX = "routes:to_route:"
CB_ROUTES_TO_BLOCKS_PREFIX = "routes:to_blocks:"


def _back_button_text(language: str) -> str:
    return "⬅️ Назад" if normalize_language(language) == "ru" else "⬅️ Back"


def _next_button_text(language: str) -> str:
    return "Дальше ➡️" if normalize_language(language) == "ru" else "Next ➡️"


def _home_button_text(language: str) -> str:
    return "🏠 Главное меню" if normalize_language(language) == "ru" else "🏠 Main menu"


def _start_button_text(language: str) -> str:
    return "▶️ Начать" if normalize_language(language) == "ru" else "▶️ Start"


def _news_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📰 Перейти к новостям"
    return "📰 Go to news"


def _questions_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "❓ Перейти к вопросам"
    return "❓ Go to questions"


def build_routes_empty_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_home_button_text(language),
                    callback_data=CB_ROUTES_HOME,
                )
            ]
        ]
    )


def build_routes_list_keyboard(
    language: str,
    *,
    route_buttons: list[tuple[int, str]],
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for route_id, route_title in route_buttons:
        rows.append(
            [
                InlineKeyboardButton(
                    text=route_title,
                    callback_data=f"{CB_ROUTES_OPEN_PREFIX}{route_id}:{page}",
                )
            ]
        )

    has_prev = page > 1
    has_next = page < total_pages
    nav_row: list[InlineKeyboardButton] = []
    if has_prev:
        nav_row.append(
            InlineKeyboardButton(
                text=_back_button_text(language),
                callback_data=f"{CB_ROUTES_LIST_PREFIX}{page - 1}",
            )
        )
    nav_row.append(
        InlineKeyboardButton(
            text=_home_button_text(language),
            callback_data=CB_ROUTES_HOME,
        )
    )
    if has_next:
        nav_row.append(
            InlineKeyboardButton(
                text=_next_button_text(language),
                callback_data=f"{CB_ROUTES_LIST_PREFIX}{page + 1}",
            )
        )
    rows.append(nav_row)
    return InlineKeyboardMarkup(rows)


def build_route_briefing_keyboard(
    language: str,
    *,
    route_id: int,
    page: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_start_button_text(language),
                    callback_data=f"{CB_ROUTES_START_PREFIX}{route_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=_news_button_text(language),
                    callback_data=f"{CB_ROUTES_NEWS_PREFIX}{route_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=_questions_button_text(language),
                    callback_data=f"{CB_ROUTES_QUESTIONS_PREFIX}{route_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=_back_button_text(language),
                    callback_data=f"{CB_ROUTES_BACK_LIST_PREFIX}{page}",
                ),
                InlineKeyboardButton(
                    text=_home_button_text(language),
                    callback_data=CB_ROUTES_HOME,
                ),
            ],
        ]
    )


def build_route_step_keyboard(
    language: str,
    *,
    route_id: int,
    step_number: int,
    has_previous: bool,
    has_next: bool,
    has_transcript: bool,
    transcript_open: bool,
    step_type: str,
    has_pilot_answer: bool,
    pilot_answer_open: bool,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if has_transcript:
        if step_type == "atis":
            text = (
                route_hide_atis_button_text(language)
                if transcript_open
                else route_show_atis_button_text(language)
            )
        elif step_type == "atc_command":
            text = (
                route_hide_command_button_text(language)
                if transcript_open
                else route_show_command_button_text(language)
            )
        else:
            text = (
                route_hide_hint_button_text(language)
                if transcript_open
                else route_show_hint_button_text(language)
            )
        rows.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"{CB_ROUTES_STEP_TR_PREFIX}{route_id}:{step_number}",
                )
            ]
        )

    if has_pilot_answer:
        answer_text = (
            route_hide_answer_button_text(language)
            if pilot_answer_open
            else route_show_answer_button_text(language)
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=answer_text,
                    callback_data=f"{CB_ROUTES_STEP_ANS_PREFIX}{route_id}:{step_number}",
                )
            ]
        )

    nav_row: list[InlineKeyboardButton] = []
    if has_previous:
        nav_row.append(
            InlineKeyboardButton(
                text=_back_button_text(language),
                callback_data=f"{CB_ROUTES_STEP_BACK_PREFIX}{route_id}:{step_number}",
            )
        )
    nav_row.append(
        InlineKeyboardButton(
            text=_next_button_text(language),
            callback_data=f"{CB_ROUTES_STEP_NEXT_PREFIX}{route_id}:{step_number}",
        )
    )
    rows.append(nav_row)
    rows.append(
        [
            InlineKeyboardButton(
                text=_home_button_text(language),
                callback_data=f"{CB_ROUTES_INTERRUPT_ASK_PREFIX}{route_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_route_interrupt_keyboard(language: str, *, route_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=route_interrupt_stay_button(language),
                    callback_data=f"{CB_ROUTES_INTERRUPT_NO_PREFIX}{route_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=route_interrupt_yes_button(language),
                    callback_data=f"{CB_ROUTES_INTERRUPT_YES_PREFIX}{route_id}",
                )
            ],
        ]
    )


def build_route_news_keyboard(
    language: str,
    *,
    route_id: int,
    has_transcript: bool,
    transcript_open: bool,
    is_full_mode: bool,
    news_list_page: int | None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if has_transcript:
        transcript_callback = (
            f"{CB_ROUTES_NEWS_TR_PREFIX}{route_id}"
            if is_full_mode
            else f"{CB_ROUTES_NEWS_TR_PREFIX}{route_id}:{max(1, int(news_list_page or 1))}"
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=(
                        route_news_hide_transcript_button_text(language)
                        if transcript_open
                        else route_news_show_transcript_button_text(language)
                    ),
                    callback_data=transcript_callback,
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=_next_button_text(language),
                callback_data=f"{CB_ROUTES_NEWS_Q_PREFIX}{route_id}",
            )
        ]
    )
    if is_full_mode:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_home_button_text(language),
                    callback_data=f"{CB_ROUTES_INTERRUPT_ASK_PREFIX}{route_id}",
                )
            ]
        )
    else:
        back_list_page = max(1, int(news_list_page or 1))
        rows.append(
            [
                InlineKeyboardButton(
                    text=route_to_news_list_button_text(language),
                    callback_data=f"{CB_ROUTES_NEWS_LIST_PREFIX}{route_id}:{back_list_page}",
                ),
                InlineKeyboardButton(
                    text=route_to_route_button_text(language),
                    callback_data=f"{CB_ROUTES_TO_ROUTE_PREFIX}{route_id}",
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=_home_button_text(language),
                    callback_data=CB_ROUTES_HOME,
                ),
            ]
        )
    return InlineKeyboardMarkup(rows)


def build_route_questions_keyboard(
    language: str,
    *,
    route_id: int,
    question_number: int,
    has_previous: bool,
    has_next: bool,
    has_ru_translation: bool,
    show_ru_translation: bool,
    is_full_mode: bool,
    show_to_blocks: bool,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if normalize_language(language) == "ru" and has_ru_translation:
        rows.append(
            [
                InlineKeyboardButton(
                    text=route_question_translate_button_text(
                        language,
                        open_translation=show_ru_translation,
                    ),
                    callback_data=f"{CB_ROUTES_Q_RU_PREFIX}{route_id}:{question_number}",
                )
            ]
        )

    nav_row: list[InlineKeyboardButton] = []
    if has_previous:
        nav_row.append(
            InlineKeyboardButton(
                text=_back_button_text(language),
                callback_data=f"{CB_ROUTES_Q_BACK_PREFIX}{route_id}:{question_number}",
            )
        )
    if has_next:
        nav_row.append(
            InlineKeyboardButton(
                text=_next_button_text(language),
                callback_data=f"{CB_ROUTES_Q_NEXT_PREFIX}{route_id}:{question_number}",
            )
        )
    else:
        nav_row.append(
            InlineKeyboardButton(
                text=route_question_finish_button_text(language),
                callback_data=f"{CB_ROUTES_Q_FINISH_PREFIX}{route_id}:{question_number}",
            )
        )
    rows.append(nav_row)
    if is_full_mode:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_home_button_text(language),
                    callback_data=f"{CB_ROUTES_INTERRUPT_ASK_PREFIX}{route_id}",
                )
            ]
        )
    else:
        if show_to_blocks:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=route_to_blocks_button_text(language),
                        callback_data=f"{CB_ROUTES_TO_BLOCKS_PREFIX}{route_id}",
                    )
                ]
            )
        rows.append(
            [
                InlineKeyboardButton(
                    text=route_to_route_button_text(language),
                    callback_data=f"{CB_ROUTES_TO_ROUTE_PREFIX}{route_id}",
                ),
                InlineKeyboardButton(
                    text=_home_button_text(language),
                    callback_data=CB_ROUTES_HOME,
                ),
            ]
        )
    return InlineKeyboardMarkup(rows)


def build_route_news_list_keyboard(
    language: str,
    *,
    route_id: int,
    news_buttons: list[tuple[int, int]],
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for news_id, news_order in news_buttons:
        rows.append(
            [
                InlineKeyboardButton(
                    text=route_news_item_button_text(language, news_order=news_order),
                    callback_data=f"{CB_ROUTES_NEWS_OPEN_PREFIX}{route_id}:{news_id}:{page}",
                )
            ]
        )

    has_prev = page > 1
    has_next = page < total_pages
    if has_prev or has_next:
        nav_row: list[InlineKeyboardButton] = []
        if has_prev:
            nav_row.append(
                InlineKeyboardButton(
                    text=_back_button_text(language),
                    callback_data=f"{CB_ROUTES_NEWS_LIST_PREFIX}{route_id}:{page - 1}",
                )
            )
        if has_next:
            nav_row.append(
                InlineKeyboardButton(
                    text=_next_button_text(language),
                    callback_data=f"{CB_ROUTES_NEWS_LIST_PREFIX}{route_id}:{page + 1}",
                )
            )
        rows.append(nav_row)

    rows.append(
        [
            InlineKeyboardButton(
                text=route_to_route_button_text(language),
                callback_data=f"{CB_ROUTES_TO_ROUTE_PREFIX}{route_id}",
            ),
            InlineKeyboardButton(
                text=_home_button_text(language),
                callback_data=CB_ROUTES_HOME,
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_route_question_blocks_list_keyboard(
    language: str,
    *,
    route_id: int,
    block_buttons: list[tuple[int, int]],
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for block_id, block_order in block_buttons:
        rows.append(
            [
                InlineKeyboardButton(
                    text=route_question_block_button_text(language, block_order=block_order),
                    callback_data=f"{CB_ROUTES_QB_OPEN_PREFIX}{route_id}:{block_id}:{page}",
                )
            ]
        )

    has_prev = page > 1
    has_next = page < total_pages
    if has_prev or has_next:
        nav_row: list[InlineKeyboardButton] = []
        if has_prev:
            nav_row.append(
                InlineKeyboardButton(
                    text=_back_button_text(language),
                    callback_data=f"{CB_ROUTES_QB_LIST_PREFIX}{route_id}:{page - 1}",
                )
            )
        if has_next:
            nav_row.append(
                InlineKeyboardButton(
                    text=_next_button_text(language),
                    callback_data=f"{CB_ROUTES_QB_LIST_PREFIX}{route_id}:{page + 1}",
                )
            )
        rows.append(nav_row)

    rows.append(
        [
            InlineKeyboardButton(
                text=route_to_route_button_text(language),
                callback_data=f"{CB_ROUTES_TO_ROUTE_PREFIX}{route_id}",
            ),
            InlineKeyboardButton(
                text=_home_button_text(language),
                callback_data=CB_ROUTES_HOME,
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_route_completion_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=route_another_route_button_text(language),
                    callback_data=CB_ROUTES_ANOTHER,
                ),
                InlineKeyboardButton(
                    text=_home_button_text(language),
                    callback_data=CB_ROUTES_HOME,
                ),
            ]
        ]
    )
