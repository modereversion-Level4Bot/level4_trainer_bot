"""Keyboard builders for grammar feature."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from features.grammar.texts import (
    back_button_text,
    back_to_topic_button_text,
    details_button_text,
    extra_materials_button_text,
    main_menu_button_text,
    next_topic_button_text,
    normalize_language,
    pagination_next_button_text,
    previous_topic_button_text,
    repeat_training_button_text,
    review_topic_again_button_text,
    start_training_button_text,
    training_topic_button_text,
    training_topic_list_button_text,
    to_grammar_button_text,
    topic_list_button_text,
)


GRAMMAR_CALLBACK_PREFIX = "grammar:"
CB_GRAMMAR_HOME = "grammar:home"
CB_GRAMMAR_LIST = "grammar:list"
CB_GRAMMAR_LIST_PAGE_PREFIX = "grammar:list:"
CB_GRAMMAR_EXTRA_LIST = "grammar:extra:list"
CB_GRAMMAR_EXTRA_LIST_PAGE_PREFIX = "grammar:extra:list:"
CB_GRAMMAR_TOPIC_PREFIX = "grammar:topic:"
CB_GRAMMAR_EXTRA_TOPIC_PREFIX = "grammar:extra:topic:"
CB_GRAMMAR_DETAILS_PREFIX = "grammar:details:"
CB_GRAMMAR_EXTRA_DETAILS_PREFIX = "grammar:extra:details:"
CB_GRAMMAR_TRAINING_PREFIX = "grammar:training:"
CB_GRAMMAR_ANSWER_PREFIX = "grammar:answer:"
CB_GRAMMAR_TRAINING_REPEAT_PREFIX = "grammar:training:repeat:"
CB_GRAMMAR_TRAINING_TOPIC_PREFIX = "grammar:training:topic:"
CB_GRAMMAR_TRAINING_LIST_PREFIX = "grammar:training:list:"


def _apply_studied_marker(title: str, *, is_studied: bool) -> str:
    if not is_studied:
        return title
    normalized = title.rstrip()
    if not normalized:
        return "✅"
    if normalized.endswith("✅"):
        return normalized
    return f"{normalized} ✅"


def _topic_button_title(language: str, topic: dict[str, object]) -> str:
    lang = normalize_language(language)
    title_ru = "" if topic.get("title_ru") is None else str(topic.get("title_ru"))
    title_en = "" if topic.get("title_en") is None else str(topic.get("title_en"))
    has_ru = title_ru.strip() != ""
    has_en = title_en.strip() != ""
    is_studied = bool(topic.get("is_studied"))
    if lang == "ru":
        title = title_ru if has_ru else title_en
        return _apply_studied_marker(title, is_studied=is_studied)
    title = title_en if has_en else title_ru
    return _apply_studied_marker(title, is_studied=is_studied)


def grammar_no_topics_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(main_menu_button_text(language), callback_data=CB_GRAMMAR_HOME)]]
    )


def grammar_topics_keyboard(
    language: str,
    *,
    topics: list[dict[str, object]],
    has_extra: bool,
    page: int = 1,
    total_pages: int = 1,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for topic in topics:
        topic_number = int(topic["topic_number"])
        rows.append(
            [
                InlineKeyboardButton(
                    text=_topic_button_title(language, topic),
                    callback_data=f"{CB_GRAMMAR_TOPIC_PREFIX}{topic_number}:{page}",
                )
            ]
        )

    if has_extra:
        rows.append(
            [
                InlineKeyboardButton(
                    text=extra_materials_button_text(language),
                    callback_data=CB_GRAMMAR_EXTRA_LIST,
                )
            ]
        )

    bottom_row: list[InlineKeyboardButton] = []
    if total_pages > 1 and page > 1:
        bottom_row.append(
            InlineKeyboardButton(
                text=back_button_text(language),
                callback_data=f"{CB_GRAMMAR_LIST_PAGE_PREFIX}{page - 1}",
            )
        )
    bottom_row.append(
        InlineKeyboardButton(main_menu_button_text(language), callback_data=CB_GRAMMAR_HOME)
    )
    if total_pages > 1 and page < total_pages:
        bottom_row.append(
            InlineKeyboardButton(
                text=pagination_next_button_text(language),
                callback_data=f"{CB_GRAMMAR_LIST_PAGE_PREFIX}{page + 1}",
            )
        )
    rows.append(bottom_row)
    return InlineKeyboardMarkup(rows)


def grammar_extra_topics_keyboard(
    language: str,
    *,
    topics: list[dict[str, object]],
    page: int = 1,
    total_pages: int = 1,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for topic in topics:
        topic_number = int(topic["topic_number"])
        rows.append(
            [
                InlineKeyboardButton(
                    text=_topic_button_title(language, topic),
                    callback_data=f"{CB_GRAMMAR_EXTRA_TOPIC_PREFIX}{topic_number}:{page}",
                )
            ]
        )

    rows.append(
        [InlineKeyboardButton(to_grammar_button_text(language), callback_data=CB_GRAMMAR_LIST)]
    )

    bottom_row: list[InlineKeyboardButton] = []
    if total_pages > 1 and page > 1:
        bottom_row.append(
            InlineKeyboardButton(
                text=back_button_text(language),
                callback_data=f"{CB_GRAMMAR_EXTRA_LIST_PAGE_PREFIX}{page - 1}",
            )
        )
    bottom_row.append(
        InlineKeyboardButton(main_menu_button_text(language), callback_data=CB_GRAMMAR_HOME)
    )
    if total_pages > 1 and page < total_pages:
        bottom_row.append(
            InlineKeyboardButton(
                text=pagination_next_button_text(language),
                callback_data=f"{CB_GRAMMAR_EXTRA_LIST_PAGE_PREFIX}{page + 1}",
            )
        )
    rows.append(bottom_row)
    return InlineKeyboardMarkup(rows)


def grammar_topic_keyboard(
    language: str,
    *,
    topic_number: int,
    has_details: bool,
    has_training: bool,
    is_extra: bool,
    page: int = 1,
    previous_topic_number: int | None = None,
    previous_topic_page: int | None = None,
    next_topic_number: int | None = None,
    next_topic_page: int | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    first_row: list[InlineKeyboardButton] = []
    if has_details:
        details_prefix = CB_GRAMMAR_EXTRA_DETAILS_PREFIX if is_extra else CB_GRAMMAR_DETAILS_PREFIX
        first_row.append(
            InlineKeyboardButton(
                text=details_button_text(language),
                callback_data=f"{details_prefix}{topic_number}:{page}",
            )
        )

    if has_training:
        first_row.append(
            InlineKeyboardButton(
                text=start_training_button_text(language),
                callback_data=f"{CB_GRAMMAR_TRAINING_PREFIX}{topic_number}:{page}:start",
            )
        )
    if first_row:
        rows.append(first_row)

    topic_prefix = CB_GRAMMAR_EXTRA_TOPIC_PREFIX if is_extra else CB_GRAMMAR_TOPIC_PREFIX
    list_text = topic_list_button_text(language)
    list_callback = (
        f"{CB_GRAMMAR_EXTRA_LIST_PAGE_PREFIX}{page}"
        if is_extra
        else f"{CB_GRAMMAR_LIST_PAGE_PREFIX}{page}"
    )
    has_previous = (
        previous_topic_number is not None
        and previous_topic_number > 0
        and previous_topic_page is not None
        and previous_topic_page > 0
    )
    has_next = (
        next_topic_number is not None
        and next_topic_number > 0
        and next_topic_page is not None
        and next_topic_page > 0
    )

    navigation_row: list[InlineKeyboardButton] = []
    if has_previous:
        navigation_row.append(
            InlineKeyboardButton(
                previous_topic_button_text(language),
                callback_data=f"{topic_prefix}{previous_topic_number}:{previous_topic_page}",
            )
        )
    navigation_row.append(InlineKeyboardButton(list_text, callback_data=list_callback))
    if has_next:
        navigation_row.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"{topic_prefix}{next_topic_number}:{next_topic_page}",
            )
        )

    rows.append(navigation_row)
    rows.append([InlineKeyboardButton(main_menu_button_text(language), callback_data=CB_GRAMMAR_HOME)])
    return InlineKeyboardMarkup(rows)


def grammar_details_keyboard(
    language: str,
    *,
    topic_number: int,
    is_extra: bool,
    has_training: bool = False,
    page: int = 1,
) -> InlineKeyboardMarkup:
    topic_prefix = CB_GRAMMAR_EXTRA_TOPIC_PREFIX if is_extra else CB_GRAMMAR_TOPIC_PREFIX
    list_text = topic_list_button_text(language)
    list_callback = (
        f"{CB_GRAMMAR_EXTRA_LIST_PAGE_PREFIX}{page}"
        if is_extra
        else f"{CB_GRAMMAR_LIST_PAGE_PREFIX}{page}"
    )
    first_row: list[InlineKeyboardButton] = [
        InlineKeyboardButton(
            back_to_topic_button_text(language),
            callback_data=f"{topic_prefix}{topic_number}:{page}",
        )
    ]
    if has_training:
        first_row.append(
            InlineKeyboardButton(
                start_training_button_text(language),
                callback_data=f"{CB_GRAMMAR_TRAINING_PREFIX}{topic_number}:{page}:start",
            )
        )
    return InlineKeyboardMarkup(
        [
            [
                *first_row,
            ],
            [
                InlineKeyboardButton(list_text, callback_data=list_callback),
                InlineKeyboardButton(
                    main_menu_button_text(language),
                    callback_data=CB_GRAMMAR_HOME,
                )
            ],
        ]
    )


def _topic_kind_token(is_extra: bool) -> str:
    return "extra" if is_extra else "main"


def grammar_training_question_keyboard(
    language: str,
    *,
    session_id: int,
    topic_number: int,
    source_page: int,
    is_extra: bool,
    answers: list[str],
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    answer_row: list[InlineKeyboardButton] = []
    for answer_index, answer_text in enumerate(answers, start=1):
        answer_row.append(
            InlineKeyboardButton(
                text=answer_text,
                callback_data=f"{CB_GRAMMAR_ANSWER_PREFIX}{session_id}:{answer_index}",
            )
        )
    if answer_row:
        rows.append(answer_row)

    topic_kind = _topic_kind_token(is_extra)
    rows.append(
        [
            InlineKeyboardButton(
                text=training_topic_button_text(language),
                callback_data=(
                    f"{CB_GRAMMAR_TRAINING_TOPIC_PREFIX}"
                    f"{topic_number}:{source_page}:{topic_kind}"
                ),
            ),
            InlineKeyboardButton(
                main_menu_button_text(language),
                callback_data=CB_GRAMMAR_HOME,
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)


def grammar_training_result_keyboard(
    language: str,
    *,
    topic_number: int,
    source_page: int,
    is_extra: bool,
    is_weak_result: bool,
    next_topic_number: int | None = None,
    next_topic_page: int | None = None,
) -> InlineKeyboardMarkup:
    topic_kind = _topic_kind_token(is_extra)
    topic_prefix = CB_GRAMMAR_EXTRA_TOPIC_PREFIX if is_extra else CB_GRAMMAR_TOPIC_PREFIX
    repeat_callback = (
        f"{CB_GRAMMAR_TRAINING_REPEAT_PREFIX}{topic_number}:{source_page}:{topic_kind}"
    )
    topic_callback = (
        f"{CB_GRAMMAR_TRAINING_TOPIC_PREFIX}{topic_number}:{source_page}:{topic_kind}"
    )
    list_callback = f"{CB_GRAMMAR_TRAINING_LIST_PREFIX}{source_page}:{topic_kind}"

    rows: list[list[InlineKeyboardButton]] = []
    if is_weak_result:
        rows.append(
            [
                InlineKeyboardButton(
                    text=review_topic_again_button_text(language),
                    callback_data=topic_callback,
                ),
                InlineKeyboardButton(
                    text=repeat_training_button_text(language),
                    callback_data=repeat_callback,
                ),
            ]
        )
    else:
        has_next_topic = (
            next_topic_number is not None
            and next_topic_number > 0
            and next_topic_page is not None
            and next_topic_page > 0
        )
        if has_next_topic:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=repeat_training_button_text(language),
                        callback_data=repeat_callback,
                    ),
                    InlineKeyboardButton(
                        text=next_topic_button_text(language),
                        callback_data=f"{topic_prefix}{next_topic_number}:{next_topic_page}",
                    ),
                ]
            )
        else:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=repeat_training_button_text(language),
                        callback_data=repeat_callback,
                    )
                ]
            )

    rows.append(
        [
            InlineKeyboardButton(
                text=training_topic_list_button_text(language),
                callback_data=list_callback,
            ),
            InlineKeyboardButton(main_menu_button_text(language), callback_data=CB_GRAMMAR_HOME),
        ]
    )
    return InlineKeyboardMarkup(rows)
