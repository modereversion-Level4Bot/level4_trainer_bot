"""Service layer for exam info feature."""

from __future__ import annotations

from telegram import Bot

from core.message_stack import render_main_ui
from features.exam_info.keyboards import (
    build_exam_info_interview_keyboard,
    build_exam_info_overview_keyboard,
    build_exam_info_post_flight_keyboard,
    build_exam_info_role_play_keyboard,
)
from features.exam_info.texts import (
    exam_info_interview_text,
    exam_info_overview_text,
    exam_info_post_flight_text,
    exam_info_role_play_text,
    normalize_language,
)


async def show_exam_info_overview(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
) -> None:
    lang = normalize_language(language)
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=exam_info_overview_text(lang),
        reply_markup=build_exam_info_overview_keyboard(lang),
        parse_mode="HTML",
    )


async def show_exam_info_interview(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
) -> None:
    lang = normalize_language(language)
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=exam_info_interview_text(lang),
        reply_markup=build_exam_info_interview_keyboard(lang),
        parse_mode="HTML",
    )


async def show_exam_info_role_play(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
) -> None:
    lang = normalize_language(language)
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=exam_info_role_play_text(lang),
        reply_markup=build_exam_info_role_play_keyboard(lang),
        parse_mode="HTML",
    )


async def show_exam_info_post_flight(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
) -> None:
    lang = normalize_language(language)
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=exam_info_post_flight_text(lang),
        reply_markup=build_exam_info_post_flight_keyboard(lang),
        parse_mode="HTML",
    )
