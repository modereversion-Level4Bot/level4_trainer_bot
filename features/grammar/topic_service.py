"""Topic and list rendering for grammar feature."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from core.message_stack import render_main_ui
from db.connection import get_connection
from db.repositories.grammar_repo import (
    count_extra_topics,
    count_questions_for_topic,
    count_studied_main_topics,
    get_topic_by_number,
    is_grammar_topic_studied,
    list_extra_topics,
    list_main_topics,
)
from features.grammar.formatting import (
    _localized_value,
    _sanitize_dynamic_html,
    _strip_leading_details_prefix,
    _strip_leading_icon,
)
from features.grammar.keyboards import (
    grammar_details_keyboard,
    grammar_extra_topics_keyboard,
    grammar_no_topics_keyboard,
    grammar_topic_keyboard,
    grammar_topics_keyboard,
)
from features.grammar.pagination import (
    GRAMMAR_TOPICS_PAGE_SIZE,
    _build_topic_navigation_context,
    _paginate_items,
    _to_positive_int,
)
from features.grammar.texts import (
    details_text,
    extra_materials_text,
    grammar_list_text,
    grammar_no_topics_text,
    missing_topic_description_text,
    normalize_language,
    topic_text,
)
from features.main_menu.service import get_user_language_by_telegram_id


def _bounded_progress(completed: int, total: int) -> int:
    if completed < 0:
        return 0
    if completed > total:
        return total
    return completed


def _topic_is_extra(topic: dict[str, object]) -> bool:
    return str(topic.get("topic_type") or "").strip().lower() == "extra"


async def show_grammar_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict[str, object],
    *,
    page: int = 1,
) -> bool:
    """Render grammar main screen with list of main topics."""
    chat = update.effective_chat
    if chat is None:
        return False

    user_id = int(user["id"])
    telegram_id = int(user["telegram_id"])
    language = get_user_language_by_telegram_id(telegram_id)
    lang = normalize_language(language)

    with get_connection() as conn:
        topics = list_main_topics(conn)
        for topic in topics:
            topic_number = _to_positive_int(topic.get("topic_number"), fallback=0)
            topic["is_studied"] = (
                topic_number > 0
                and is_grammar_topic_studied(conn, user_id=user_id, topic_number=topic_number)
            )
        total = len(topics)
        completed = count_studied_main_topics(conn, user_id=user_id)
        has_extra = count_extra_topics(conn) > 0

    if total <= 0:
        await render_main_ui(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            text=grammar_no_topics_text(lang),
            reply_markup=grammar_no_topics_keyboard(lang),
            parse_mode="HTML",
        )
        return True

    paged_topics, safe_page, total_pages = _paginate_items(
        topics,
        page=page,
        page_size=GRAMMAR_TOPICS_PAGE_SIZE,
    )

    await render_main_ui(
        bot=context.bot,
        chat_id=chat.id,
        user_id=user_id,
        text=grammar_list_text(
            lang,
            completed=_bounded_progress(completed, total),
            total=total,
            page=safe_page,
            total_pages=total_pages,
        ),
        reply_markup=grammar_topics_keyboard(
            lang,
            topics=paged_topics,
            has_extra=has_extra,
            page=safe_page,
            total_pages=total_pages,
        ),
        parse_mode="HTML",
    )
    return True


async def show_extra_materials(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict[str, object],
    *,
    page: int = 1,
) -> bool:
    """Render extra materials list."""
    chat = update.effective_chat
    if chat is None:
        return False

    user_id = int(user["id"])
    telegram_id = int(user["telegram_id"])
    language = get_user_language_by_telegram_id(telegram_id)
    lang = normalize_language(language)

    with get_connection() as conn:
        topics = list_extra_topics(conn)

    if not topics:
        return False

    paged_topics, safe_page, total_pages = _paginate_items(
        topics,
        page=page,
        page_size=GRAMMAR_TOPICS_PAGE_SIZE,
    )

    await render_main_ui(
        bot=context.bot,
        chat_id=chat.id,
        user_id=user_id,
        text=extra_materials_text(
            lang,
            page=safe_page,
            total_pages=total_pages,
        ),
        reply_markup=grammar_extra_topics_keyboard(
            lang,
            topics=paged_topics,
            page=safe_page,
            total_pages=total_pages,
        ),
        parse_mode="HTML",
    )
    return True


async def show_topic(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict[str, object],
    topic_number: int,
    *,
    is_extra: bool = False,
    page: int = 1,
) -> bool:
    """Render one grammar topic screen."""
    chat = update.effective_chat
    if chat is None:
        return False

    user_id = int(user["id"])
    telegram_id = int(user["telegram_id"])
    language = get_user_language_by_telegram_id(telegram_id)
    lang = normalize_language(language)

    with get_connection() as conn:
        topic = get_topic_by_number(conn, topic_number)
        if topic is None:
            return False
        if _topic_is_extra(topic) != is_extra:
            return False

        questions_count = count_questions_for_topic(conn, topic_number)
        topics_for_navigation = list_extra_topics(conn) if is_extra else list_main_topics(conn)
        navigation = _build_topic_navigation_context(
            topics_for_navigation,
            topic_number=topic_number,
        )
        safe_page = navigation.current_page
        if safe_page <= 0:
            _, safe_page, _ = _paginate_items(
                topics_for_navigation,
                page=page,
                page_size=GRAMMAR_TOPICS_PAGE_SIZE,
            )

    title = _localized_value(
        lang,
        ru_value=topic.get("title_ru"),  # type: ignore[arg-type]
        en_value=topic.get("title_en"),  # type: ignore[arg-type]
        default_value=f"Topic {topic_number}",
    )
    header_title = _sanitize_dynamic_html(_strip_leading_icon(title))
    simple_explanation = _localized_value(
        lang,
        ru_value=topic.get("simple_explanation_ru"),  # type: ignore[arg-type]
        en_value=topic.get("simple_explanation_en"),  # type: ignore[arg-type]
        default_value=missing_topic_description_text(lang),
    )
    simple_explanation = _sanitize_dynamic_html(simple_explanation)
    has_details = bool(
        (str(topic.get("detailed_explanation_ru") or "").strip())
        or (str(topic.get("detailed_explanation_en") or "").strip())
    )
    has_training = questions_count > 0

    await render_main_ui(
        bot=context.bot,
        chat_id=chat.id,
        user_id=user_id,
        text=topic_text(
            lang,
            title=header_title,
            simple_explanation=simple_explanation,
        ),
        reply_markup=grammar_topic_keyboard(
            lang,
            topic_number=topic_number,
            has_details=has_details,
            has_training=has_training,
            is_extra=is_extra,
            page=safe_page,
            previous_topic_number=navigation.previous_topic_number,
            previous_topic_page=navigation.previous_topic_page,
            next_topic_number=navigation.next_topic_number,
            next_topic_page=navigation.next_topic_page,
        ),
        parse_mode="HTML",
    )
    return True


async def show_topic_details(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict[str, object],
    topic_number: int,
    *,
    is_extra: bool = False,
    page: int = 1,
) -> bool:
    """Render detailed grammar explanation for topic."""
    chat = update.effective_chat
    if chat is None:
        return False

    user_id = int(user["id"])
    telegram_id = int(user["telegram_id"])
    language = get_user_language_by_telegram_id(telegram_id)
    lang = normalize_language(language)

    with get_connection() as conn:
        topic = get_topic_by_number(conn, topic_number)
        if topic is None:
            return False
        if _topic_is_extra(topic) != is_extra:
            return False
        questions_count = count_questions_for_topic(conn, topic_number)
        topics_for_page = list_extra_topics(conn) if is_extra else list_main_topics(conn)
        _, safe_page, _ = _paginate_items(
            topics_for_page,
            page=page,
            page_size=GRAMMAR_TOPICS_PAGE_SIZE,
        )

    detailed_ru = str(topic.get("detailed_explanation_ru") or "").strip()
    detailed_en = str(topic.get("detailed_explanation_en") or "").strip()
    if not detailed_ru and not detailed_en:
        return False

    title = _localized_value(
        lang,
        ru_value=topic.get("title_ru"),  # type: ignore[arg-type]
        en_value=topic.get("title_en"),  # type: ignore[arg-type]
        default_value=f"Topic {topic_number}",
    )
    header_title = _sanitize_dynamic_html(_strip_leading_icon(title))
    detailed = _localized_value(
        lang,
        ru_value=topic.get("detailed_explanation_ru"),  # type: ignore[arg-type]
        en_value=topic.get("detailed_explanation_en"),  # type: ignore[arg-type]
        default_value="",
    )
    detailed = _strip_leading_details_prefix(detailed)
    detailed = _sanitize_dynamic_html(detailed)

    await render_main_ui(
        bot=context.bot,
        chat_id=chat.id,
        user_id=user_id,
        text=details_text(
            lang,
            title=header_title,
            detailed_explanation=detailed,
        ),
        reply_markup=grammar_details_keyboard(
            lang,
            topic_number=topic_number,
            is_extra=is_extra,
            has_training=questions_count > 0,
            page=safe_page,
        ),
        parse_mode="HTML",
    )
    return True
