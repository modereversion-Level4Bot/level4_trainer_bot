"""Context model for main menu rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MainMenuContext:
    grammar_total: int
    grammar_completed: int
    questions_total: int
    questions_completed: int
    routes_total: int
    routes_completed: int
    has_grammar_content: bool
    has_questions_content: bool
    is_admin: bool
    bot_version: str
