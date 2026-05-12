"""Handlers for routes feature."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from core.guards import run_guard_chain
from core.safe_telegram import safe_answer_callback
from features.main_menu.service import (
    get_user_language_by_telegram_id,
    get_user_row_by_telegram_id,
)
from features.routes.keyboards import (
    CB_ROUTES_ANOTHER,
    CB_ROUTES_BACK_LIST_PREFIX,
    CB_ROUTES_HOME,
    CB_ROUTES_INTERRUPT_ASK_PREFIX,
    CB_ROUTES_INTERRUPT_NO_PREFIX,
    CB_ROUTES_INTERRUPT_YES_PREFIX,
    CB_ROUTES_LIST_PREFIX,
    CB_ROUTES_NEWS_PREFIX,
    CB_ROUTES_NEWS_LIST_PREFIX,
    CB_ROUTES_NEWS_OPEN_PREFIX,
    CB_ROUTES_NEWS_Q_PREFIX,
    CB_ROUTES_NEWS_TR_PREFIX,
    CB_ROUTES_OPEN_PREFIX,
    CB_ROUTES_QUESTIONS_PREFIX,
    CB_ROUTES_QB_LIST_PREFIX,
    CB_ROUTES_QB_OPEN_PREFIX,
    CB_ROUTES_Q_BACK_PREFIX,
    CB_ROUTES_Q_FINISH_PREFIX,
    CB_ROUTES_Q_NEXT_PREFIX,
    CB_ROUTES_Q_RU_PREFIX,
    CB_ROUTES_STEP_ANS_PREFIX,
    CB_ROUTES_STEP_BACK_PREFIX,
    CB_ROUTES_STEP_NEXT_PREFIX,
    CB_ROUTES_STEP_TR_PREFIX,
    CB_ROUTES_START_PREFIX,
    CB_ROUTES_TO_BLOCKS_PREFIX,
    CB_ROUTES_TO_ROUTE_PREFIX,
    ROUTES_CALLBACK_PREFIX,
)
from features.routes.handlers_parsers import (
    _parse_int_payload,
    _parse_route_item_page_payload,
    _parse_route_open_payload,
    _parse_route_page_payload,
    _parse_route_step_payload,
)
from features.routes.service import (
    finish_route_questions,
    is_routes_ui_enabled,
    move_route_step,
    move_route_question,
    open_route_news_from_briefing,
    open_route_news_from_list,
    open_route_questions_from_briefing,
    open_route_questions_for_block,
    open_route_questions_from_news,
    return_to_question_blocks_list,
    return_to_route_briefing,
    route_interrupt_confirm,
    route_interrupt_stay,
    routes_go_home,
    show_route_interrupt_confirmation,
    show_route_briefing,
    show_route_news_list,
    show_route_question_blocks_list,
    show_routes_list,
    start_route_scenario,
    toggle_route_news_transcript,
    toggle_route_question_translation,
    toggle_route_pilot_answer,
    toggle_route_transcript,
)
from features.routes.texts import (
    route_scenario_placeholder_alert,
    stale_routes_navigation_alert,
)

async def routes_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callbacks for Routes list/briefing local Phase 2."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if query is None or user is None or chat is None:
        return

    callback_data = query.data or ""
    if not callback_data.startswith(ROUTES_CALLBACK_PREFIX):
        return

    if not await run_guard_chain(update, context):
        await safe_answer_callback(query)
        return

    user_row = get_user_row_by_telegram_id(user.id)
    if user_row is None:
        await safe_answer_callback(query)
        return
    user_id = int(user_row["id"])
    language = get_user_language_by_telegram_id(user.id)

    if not is_routes_ui_enabled():
        await safe_answer_callback(
            query,
            text=stale_routes_navigation_alert(language),
            show_alert=True,
        )
        await routes_go_home(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            telegram_id=user.id,
        )
        return

    if callback_data == CB_ROUTES_HOME:
        await safe_answer_callback(query)
        await routes_go_home(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            telegram_id=user.id,
        )
        return

    if callback_data == CB_ROUTES_ANOTHER:
        await safe_answer_callback(query)
        await show_routes_list(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            page=1,
        )
        return

    page = _parse_int_payload(callback_data, CB_ROUTES_LIST_PREFIX)
    if page is not None:
        await safe_answer_callback(query)
        await show_routes_list(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            page=page,
        )
        return

    back_page = _parse_int_payload(callback_data, CB_ROUTES_BACK_LIST_PREFIX)
    if back_page is not None:
        await safe_answer_callback(query)
        await show_routes_list(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            page=back_page,
        )
        return

    open_payload = _parse_route_open_payload(callback_data)
    if open_payload is not None:
        route_id, page = open_payload
        shown = await show_route_briefing(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            page=page,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_routes_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                page=1,
            )
        return

    start_route_id = _parse_int_payload(callback_data, CB_ROUTES_START_PREFIX)
    if start_route_id is not None:
        started, alert_text = await start_route_scenario(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=start_route_id,
        )
        if started:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or route_scenario_placeholder_alert(language),
                show_alert=True,
            )
        return

    news_route_id = _parse_int_payload(callback_data, CB_ROUTES_NEWS_PREFIX)
    if news_route_id is not None:
        opened, alert_text = await open_route_news_from_briefing(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=news_route_id,
        )
        if opened:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    questions_route_id = _parse_int_payload(callback_data, CB_ROUTES_QUESTIONS_PREFIX)
    if questions_route_id is not None:
        opened, alert_text = await open_route_questions_from_briefing(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=questions_route_id,
        )
        if opened:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    to_route_id = _parse_int_payload(callback_data, CB_ROUTES_TO_ROUTE_PREFIX)
    if to_route_id is not None:
        returned, alert_text = await return_to_route_briefing(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=to_route_id,
        )
        if returned:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_routes_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                page=1,
            )
        return

    to_blocks_route_id = _parse_int_payload(callback_data, CB_ROUTES_TO_BLOCKS_PREFIX)
    if to_blocks_route_id is not None:
        returned, alert_text = await return_to_question_blocks_list(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=to_blocks_route_id,
        )
        if returned:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_routes_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                page=1,
            )
        return

    news_list_payload = _parse_route_page_payload(callback_data, CB_ROUTES_NEWS_LIST_PREFIX)
    if news_list_payload is not None:
        route_id, page = news_list_payload
        shown, alert_text = await show_route_news_list(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            page=page,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    news_open_payload = _parse_route_item_page_payload(callback_data, CB_ROUTES_NEWS_OPEN_PREFIX)
    if news_open_payload is not None:
        route_id, news_id, page = news_open_payload
        opened, alert_text = await open_route_news_from_list(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            news_id=news_id,
            page=page,
        )
        if opened:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_route_news_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                route_id=route_id,
                page=page,
            )
        return

    blocks_list_payload = _parse_route_page_payload(callback_data, CB_ROUTES_QB_LIST_PREFIX)
    if blocks_list_payload is not None:
        route_id, page = blocks_list_payload
        shown, alert_text = await show_route_question_blocks_list(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            page=page,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    blocks_open_payload = _parse_route_item_page_payload(callback_data, CB_ROUTES_QB_OPEN_PREFIX)
    if blocks_open_payload is not None:
        route_id, block_id, _page = blocks_open_payload
        opened, alert_text = await open_route_questions_for_block(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            block_id=block_id,
        )
        if opened:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    if callback_data.startswith(CB_ROUTES_NEWS_TR_PREFIX):
        raw_payload = callback_data[len(CB_ROUTES_NEWS_TR_PREFIX) :].strip()
        if not raw_payload:
            await safe_answer_callback(
                query,
                text=stale_routes_navigation_alert(language),
                show_alert=True,
            )
            return
        parts = raw_payload.split(":")
        try:
            news_transcript_route_id = int(parts[0])
        except ValueError:
            news_transcript_route_id = 0
        if news_transcript_route_id <= 0:
            await safe_answer_callback(
                query,
                text=stale_routes_navigation_alert(language),
                show_alert=True,
            )
            return
        news_list_page = None
        if len(parts) == 2:
            try:
                parsed_page = int(parts[1])
                if parsed_page > 0:
                    news_list_page = parsed_page
            except ValueError:
                news_list_page = None
        toggled, alert_text = await toggle_route_news_transcript(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=news_transcript_route_id,
            news_list_page=news_list_page,
        )
        if toggled:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_routes_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                page=1,
            )
        return

    news_questions_route_id = _parse_int_payload(callback_data, CB_ROUTES_NEWS_Q_PREFIX)
    if news_questions_route_id is not None:
        opened, alert_text = await open_route_questions_from_news(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=news_questions_route_id,
        )
        if opened:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    step_next_payload = _parse_route_step_payload(callback_data, CB_ROUTES_STEP_NEXT_PREFIX)
    if step_next_payload is not None:
        route_id, step_number = step_next_payload
        moved, alert_text = await move_route_step(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            callback_step_number=step_number,
            direction="next",
        )
        if moved:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    step_back_payload = _parse_route_step_payload(callback_data, CB_ROUTES_STEP_BACK_PREFIX)
    if step_back_payload is not None:
        route_id, step_number = step_back_payload
        moved, alert_text = await move_route_step(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            callback_step_number=step_number,
            direction="back",
        )
        if moved:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    step_transcript_payload = _parse_route_step_payload(callback_data, CB_ROUTES_STEP_TR_PREFIX)
    if step_transcript_payload is not None:
        route_id, step_number = step_transcript_payload
        toggled, alert_text = await toggle_route_transcript(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            callback_step_number=step_number,
        )
        if toggled:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_routes_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                page=1,
            )
        return

    step_answer_payload = _parse_route_step_payload(callback_data, CB_ROUTES_STEP_ANS_PREFIX)
    if step_answer_payload is not None:
        route_id, step_number = step_answer_payload
        toggled, alert_text = await toggle_route_pilot_answer(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            callback_step_number=step_number,
        )
        if toggled:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_routes_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                page=1,
            )
        return

    question_next_payload = _parse_route_step_payload(callback_data, CB_ROUTES_Q_NEXT_PREFIX)
    if question_next_payload is not None:
        route_id, question_number = question_next_payload
        moved, alert_text = await move_route_question(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            callback_question_number=question_number,
            direction="next",
        )
        if moved:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    question_back_payload = _parse_route_step_payload(callback_data, CB_ROUTES_Q_BACK_PREFIX)
    if question_back_payload is not None:
        route_id, question_number = question_back_payload
        moved, alert_text = await move_route_question(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            callback_question_number=question_number,
            direction="back",
        )
        if moved:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    question_ru_payload = _parse_route_step_payload(callback_data, CB_ROUTES_Q_RU_PREFIX)
    if question_ru_payload is not None:
        route_id, question_number = question_ru_payload
        toggled, alert_text = await toggle_route_question_translation(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            callback_question_number=question_number,
        )
        if toggled:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_routes_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                page=1,
            )
        return

    question_finish_payload = _parse_route_step_payload(callback_data, CB_ROUTES_Q_FINISH_PREFIX)
    if question_finish_payload is not None:
        route_id, question_number = question_finish_payload
        finished, alert_text = await finish_route_questions(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            callback_question_number=question_number,
        )
        if finished:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    interrupt_ask_route_id = _parse_int_payload(callback_data, CB_ROUTES_INTERRUPT_ASK_PREFIX)
    if interrupt_ask_route_id is not None:
        shown, alert_text = await show_route_interrupt_confirmation(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            telegram_id=user.id,
            language=language,
            route_id=interrupt_ask_route_id,
        )
        if shown:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_routes_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                page=1,
            )
        return

    interrupt_no_route_id = _parse_int_payload(callback_data, CB_ROUTES_INTERRUPT_NO_PREFIX)
    if interrupt_no_route_id is not None:
        restored, alert_text = await route_interrupt_stay(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            route_id=interrupt_no_route_id,
        )
        if restored:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
            await show_routes_list(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                page=1,
            )
        return

    interrupt_yes_route_id = _parse_int_payload(callback_data, CB_ROUTES_INTERRUPT_YES_PREFIX)
    if interrupt_yes_route_id is not None:
        interrupted, alert_text = await route_interrupt_confirm(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            telegram_id=user.id,
            route_id=interrupt_yes_route_id,
        )
        if interrupted:
            await safe_answer_callback(query)
        else:
            await safe_answer_callback(
                query,
                text=alert_text or stale_routes_navigation_alert(language),
                show_alert=True,
            )
        return

    await safe_answer_callback(
        query,
        text=stale_routes_navigation_alert(language),
        show_alert=True,
    )
    await show_routes_list(
        bot=context.bot,
        chat_id=chat.id,
        user_id=user_id,
        language=language,
        page=1,
    )


def register_handlers(application: Application) -> None:
    """Register handlers for routes feature callbacks."""
    application.add_handler(
        CallbackQueryHandler(
            routes_callback_router,
            pattern=r"^routes:",
        ),
        group=-1,
    )
