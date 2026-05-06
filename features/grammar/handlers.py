"""Handlers for grammar feature."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from core.guards import run_guard_chain
from core.safe_telegram import safe_answer_callback
from features.grammar.keyboards import (
    CB_GRAMMAR_ANSWER_PREFIX,
    CB_GRAMMAR_DETAILS_PREFIX,
    CB_GRAMMAR_EXTRA_DETAILS_PREFIX,
    CB_GRAMMAR_EXTRA_LIST,
    CB_GRAMMAR_EXTRA_LIST_PAGE_PREFIX,
    CB_GRAMMAR_EXTRA_TOPIC_PREFIX,
    CB_GRAMMAR_HOME,
    CB_GRAMMAR_LIST,
    CB_GRAMMAR_LIST_PAGE_PREFIX,
    CB_GRAMMAR_TOPIC_PREFIX,
    CB_GRAMMAR_TRAINING_LIST_PREFIX,
    CB_GRAMMAR_TRAINING_PREFIX,
    CB_GRAMMAR_TRAINING_REPEAT_PREFIX,
    CB_GRAMMAR_TRAINING_TOPIC_PREFIX,
    GRAMMAR_CALLBACK_PREFIX,
)
from features.grammar.service import (
    create_new_training_session,
    process_answer,
    show_extra_materials,
    show_grammar_list,
    show_topic,
    show_topic_details,
    show_training_question,
    show_training_result,
)
from features.grammar.texts import (
    training_no_questions_alert,
    training_question_unavailable_alert,
    training_session_expired_alert,
    unavailable_alert,
)
from features.main_menu.keyboards import MENU_GRAMMAR_CALLBACK
from features.main_menu.service import (
    get_user_language_by_telegram_id,
    get_user_row_by_telegram_id,
    show_main_menu,
)

GRAMMAR_HANDLER_GROUP = -1


def _parse_topic_payload(callback_data: str, prefix: str) -> tuple[int, int] | None:
    if not callback_data.startswith(prefix):
        return None
    raw_value = callback_data[len(prefix) :].strip()
    if not raw_value:
        return None

    parts = raw_value.split(":")
    if len(parts) == 1:
        try:
            return int(parts[0]), 1
        except ValueError:
            return None
    if len(parts) != 2:
        return None

    try:
        topic_number = int(parts[0])
        page = int(parts[1])
    except ValueError:
        return None
    return topic_number, page


def _parse_page_number(callback_data: str, prefix: str) -> int | None:
    if not callback_data.startswith(prefix):
        return None
    raw_value = callback_data[len(prefix) :].strip()
    if not raw_value:
        return None
    try:
        return int(raw_value)
    except ValueError:
        return None


def _parse_topic_kind(kind: str | None) -> bool | None:
    normalized = (kind or "").strip().lower()
    if normalized in {"extra", "e"}:
        return True
    if normalized in {"main", "m", ""}:
        return False
    return None


def _parse_training_start_payload(callback_data: str) -> tuple[int, int] | None:
    if not callback_data.startswith(CB_GRAMMAR_TRAINING_PREFIX):
        return None

    raw_value = callback_data[len(CB_GRAMMAR_TRAINING_PREFIX) :].strip()
    if not raw_value:
        return None
    if raw_value.startswith(("repeat:", "topic:", "list:")):
        return None

    parts = raw_value.split(":")
    if len(parts) == 1:
        try:
            return int(parts[0]), 1
        except ValueError:
            return None
    if len(parts) == 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None
    if len(parts) == 3 and parts[2].lower() == "start":
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None
    return None


def _parse_training_topic_payload(
    callback_data: str,
    prefix: str,
) -> tuple[int, int, bool] | None:
    if not callback_data.startswith(prefix):
        return None
    raw_value = callback_data[len(prefix) :].strip()
    if not raw_value:
        return None

    parts = raw_value.split(":")
    try:
        if len(parts) == 1:
            return int(parts[0]), 1, False
        if len(parts) == 2:
            return int(parts[0]), int(parts[1]), False
        if len(parts) == 3:
            is_extra = _parse_topic_kind(parts[2])
            if is_extra is None:
                return None
            return int(parts[0]), int(parts[1]), is_extra
    except ValueError:
        return None
    return None


def _parse_training_list_payload(callback_data: str) -> tuple[int, bool] | None:
    if not callback_data.startswith(CB_GRAMMAR_TRAINING_LIST_PREFIX):
        return None
    raw_value = callback_data[len(CB_GRAMMAR_TRAINING_LIST_PREFIX) :].strip()
    if not raw_value:
        return None

    parts = raw_value.split(":")
    try:
        if len(parts) == 1:
            return int(parts[0]), False
        if len(parts) == 2:
            is_extra = _parse_topic_kind(parts[1])
            if is_extra is None:
                return None
            return int(parts[0]), is_extra
    except ValueError:
        return None
    return None


def _parse_answer_payload(callback_data: str) -> tuple[int, int] | None:
    if not callback_data.startswith(CB_GRAMMAR_ANSWER_PREFIX):
        return None
    raw_value = callback_data[len(CB_GRAMMAR_ANSWER_PREFIX) :].strip()
    if not raw_value:
        return None
    parts = raw_value.split(":")
    if len(parts) != 2:
        return None
    try:
        session_id = int(parts[0])
        answer_number = int(parts[1])
    except ValueError:
        return None
    return session_id, answer_number


async def _show_unavailable_and_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    user: dict[str, object],
    language: str,
    back_to_extra: bool = False,
) -> None:
    query = update.callback_query
    if query is not None:
        await safe_answer_callback(
            query,
            text=unavailable_alert(language),
            show_alert=True,
        )

    if back_to_extra:
        shown = await show_extra_materials(update, context, user)
        if shown:
            return
    await show_grammar_list(update, context, user)


async def grammar_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route grammar callbacks and main menu grammar entry point."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if query is None or user is None or chat is None:
        return

    callback_data = query.data or ""
    if callback_data != MENU_GRAMMAR_CALLBACK and not callback_data.startswith(
        GRAMMAR_CALLBACK_PREFIX
    ):
        return

    if not await run_guard_chain(update, context):
        await safe_answer_callback(query)
        return

    user_row = get_user_row_by_telegram_id(user.id)
    if user_row is None:
        await safe_answer_callback(query)
        return

    language = get_user_language_by_telegram_id(user.id)
    user_payload = {
        "id": int(user_row["id"]),
        "telegram_id": int(user_row["telegram_id"]),
    }

    if callback_data in {MENU_GRAMMAR_CALLBACK, CB_GRAMMAR_LIST}:
        await safe_answer_callback(query)
        await show_grammar_list(update, context, user_payload)
        return

    list_page = _parse_page_number(callback_data, CB_GRAMMAR_LIST_PAGE_PREFIX)
    if list_page is not None:
        await safe_answer_callback(query)
        await show_grammar_list(
            update,
            context,
            user_payload,
            page=list_page,
        )
        return

    if callback_data == CB_GRAMMAR_EXTRA_LIST:
        shown = await show_extra_materials(update, context, user_payload)
        if shown:
            await safe_answer_callback(query)
        else:
            await _show_unavailable_and_back(
                update,
                context,
                user=user_payload,
                language=language,
            )
        return

    extra_list_page = _parse_page_number(callback_data, CB_GRAMMAR_EXTRA_LIST_PAGE_PREFIX)
    if extra_list_page is not None:
        shown = await show_extra_materials(
            update,
            context,
            user_payload,
            page=extra_list_page,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await _show_unavailable_and_back(
                update,
                context,
                user=user_payload,
                language=language,
            )
        return

    if callback_data == CB_GRAMMAR_HOME:
        await safe_answer_callback(query)
        await show_main_menu(
            bot=context.bot,
            chat_id=chat.id,
            user_id=int(user_payload["id"]),
            telegram_id=user.id,
        )
        return

    training_topic_payload = _parse_training_topic_payload(
        callback_data,
        CB_GRAMMAR_TRAINING_TOPIC_PREFIX,
    )
    if training_topic_payload is not None:
        training_topic_number, training_topic_page, training_topic_is_extra = (
            training_topic_payload
        )
        shown = await show_topic(
            update,
            context,
            user_payload,
            training_topic_number,
            is_extra=training_topic_is_extra,
            page=training_topic_page,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await _show_unavailable_and_back(
                update,
                context,
                user=user_payload,
                language=language,
                back_to_extra=training_topic_is_extra,
            )
        return

    training_list_payload = _parse_training_list_payload(callback_data)
    if training_list_payload is not None:
        training_list_page, training_list_is_extra = training_list_payload
        if training_list_is_extra:
            shown = await show_extra_materials(
                update,
                context,
                user_payload,
                page=training_list_page,
            )
            if shown:
                await safe_answer_callback(query)
            else:
                await _show_unavailable_and_back(
                    update,
                    context,
                    user=user_payload,
                    language=language,
                    back_to_extra=True,
                )
            return

        await safe_answer_callback(query)
        await show_grammar_list(
            update,
            context,
            user_payload,
            page=training_list_page,
        )
        return

    training_repeat_payload = _parse_training_topic_payload(
        callback_data,
        CB_GRAMMAR_TRAINING_REPEAT_PREFIX,
    )
    if training_repeat_payload is not None:
        repeat_topic_number, repeat_page, repeat_is_extra = training_repeat_payload
        status, session = create_new_training_session(
            int(user_payload["id"]),
            repeat_topic_number,
            source_page=repeat_page,
            is_extra=repeat_is_extra,
        )
        if status == "topic_unavailable":
            await _show_unavailable_and_back(
                update,
                context,
                user=user_payload,
                language=language,
                back_to_extra=repeat_is_extra,
            )
            return
        if status == "no_questions":
            await safe_answer_callback(
                query,
                text=training_no_questions_alert(language),
                show_alert=True,
            )
            return
        if session is None or not await show_training_question(update, context, user_payload, session):
            await safe_answer_callback(
                query,
                text=training_question_unavailable_alert(language),
                show_alert=True,
            )
            return
        await safe_answer_callback(query)
        return

    training_start_payload = _parse_training_start_payload(callback_data)
    if training_start_payload is not None:
        training_topic_number, training_page = training_start_payload
        status, session = create_new_training_session(
            int(user_payload["id"]),
            training_topic_number,
            source_page=training_page,
        )
        if status == "topic_unavailable":
            await _show_unavailable_and_back(
                update,
                context,
                user=user_payload,
                language=language,
            )
            return
        if status == "no_questions":
            await safe_answer_callback(
                query,
                text=training_no_questions_alert(language),
                show_alert=True,
            )
            return
        if session is None or not await show_training_question(update, context, user_payload, session):
            await safe_answer_callback(
                query,
                text=training_question_unavailable_alert(language),
                show_alert=True,
            )
            return
        await safe_answer_callback(query)
        return

    answer_payload = _parse_answer_payload(callback_data)
    if answer_payload is not None:
        session_id, answer_number = answer_payload
        outcome = process_answer(
            user_id=int(user_payload["id"]),
            language=language,
            session_id=session_id,
            answer_number=answer_number,
        )
        if outcome.status in {"session_expired", "question_unavailable"}:
            await safe_answer_callback(
                query,
                text=outcome.popup_text,
                show_alert=outcome.show_alert,
            )
            return

        if outcome.session is None:
            await safe_answer_callback(
                query,
                text=training_session_expired_alert(language),
                show_alert=True,
            )
            return

        await safe_answer_callback(
            query,
            text=outcome.popup_text,
            show_alert=outcome.show_alert,
        )
        if outcome.status == "next_question":
            shown = await show_training_question(update, context, user_payload, outcome.session)
            if shown:
                return
            is_extra = str(outcome.session.get("topic_type") or "").strip().lower() == "extra"
            topic_number = int(outcome.session.get("topic_number") or 0)
            page = int(outcome.session.get("source_page") or 1)
            restored = await show_topic(
                update,
                context,
                user_payload,
                topic_number,
                is_extra=is_extra,
                page=page,
            )
            if not restored:
                if is_extra:
                    await show_extra_materials(update, context, user_payload, page=page)
                else:
                    await show_grammar_list(update, context, user_payload, page=page)
            return

        if outcome.status == "show_result":
            shown = await show_training_result(
                update,
                context,
                user_payload,
                outcome.session,
                result_kind=outcome.result_kind or "weak",
                mark_applied=outcome.mark_applied,
            )
            if shown:
                return
            is_extra = str(outcome.session.get("topic_type") or "").strip().lower() == "extra"
            topic_number = int(outcome.session.get("topic_number") or 0)
            page = int(outcome.session.get("source_page") or 1)
            restored = await show_topic(
                update,
                context,
                user_payload,
                topic_number,
                is_extra=is_extra,
                page=page,
            )
            if not restored:
                if is_extra:
                    await show_extra_materials(update, context, user_payload, page=page)
                else:
                    await show_grammar_list(update, context, user_payload, page=page)
            return

        await safe_answer_callback(
            query,
            text=training_session_expired_alert(language),
            show_alert=True,
        )
        return

    main_topic_payload = _parse_topic_payload(callback_data, CB_GRAMMAR_TOPIC_PREFIX)
    if main_topic_payload is not None:
        main_topic_number, main_topic_page = main_topic_payload
        shown = await show_topic(
            update,
            context,
            user_payload,
            main_topic_number,
            is_extra=False,
            page=main_topic_page,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await _show_unavailable_and_back(
                update,
                context,
                user=user_payload,
                language=language,
            )
        return

    extra_topic_payload = _parse_topic_payload(callback_data, CB_GRAMMAR_EXTRA_TOPIC_PREFIX)
    if extra_topic_payload is not None:
        extra_topic_number, extra_topic_page = extra_topic_payload
        shown = await show_topic(
            update,
            context,
            user_payload,
            extra_topic_number,
            is_extra=True,
            page=extra_topic_page,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await _show_unavailable_and_back(
                update,
                context,
                user=user_payload,
                language=language,
                back_to_extra=True,
            )
        return

    main_details_payload = _parse_topic_payload(callback_data, CB_GRAMMAR_DETAILS_PREFIX)
    if main_details_payload is not None:
        main_details_number, main_details_page = main_details_payload
        shown = await show_topic_details(
            update,
            context,
            user_payload,
            main_details_number,
            is_extra=False,
            page=main_details_page,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await _show_unavailable_and_back(
                update,
                context,
                user=user_payload,
                language=language,
            )
        return

    extra_details_payload = _parse_topic_payload(callback_data, CB_GRAMMAR_EXTRA_DETAILS_PREFIX)
    if extra_details_payload is not None:
        extra_details_number, extra_details_page = extra_details_payload
        shown = await show_topic_details(
            update,
            context,
            user_payload,
            extra_details_number,
            is_extra=True,
            page=extra_details_page,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await _show_unavailable_and_back(
                update,
                context,
                user=user_payload,
                language=language,
                back_to_extra=True,
            )
        return

    await _show_unavailable_and_back(
        update,
        context,
        user=user_payload,
        language=language,
    )


def register_handlers(application: Application) -> None:
    """Register handlers for grammar feature."""
    application.add_handler(
        CallbackQueryHandler(grammar_callback_router, pattern=r"^(menu:grammar|grammar:)"),
        group=GRAMMAR_HANDLER_GROUP,
    )
