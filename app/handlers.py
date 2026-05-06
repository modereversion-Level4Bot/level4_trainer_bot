"""Telegram handler registry."""

from __future__ import annotations

from telegram.ext import Application

from features.clean_chat.handlers import register_handlers as register_clean_chat_handlers
from features.exam_info.handlers import register_handlers as register_exam_info_handlers
from features.grammar.handlers import register_handlers as register_grammar_handlers
from features.main_menu.handlers import register_handlers as register_main_menu_handlers
from features.onboarding.handlers import register_handlers as register_onboarding_handlers
from features.questions.handlers import register_handlers as register_questions_handlers
from features.settings.handlers import register_handlers as register_settings_handlers
from features.start.handlers import register_handlers as register_start_handlers


def register_handlers(application: Application) -> None:
    """Attach all feature handlers to the application."""
    register_start_handlers(application)
    register_onboarding_handlers(application)
    register_settings_handlers(application)
    register_grammar_handlers(application)
    register_questions_handlers(application)
    register_main_menu_handlers(application)
    register_exam_info_handlers(application)
    register_clean_chat_handlers(application)

    # TODO: Register handlers for remaining features:
    # routes, admin, feedback, ads, announcements, notifications.
