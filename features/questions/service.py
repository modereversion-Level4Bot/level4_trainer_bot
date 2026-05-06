"""Compatibility facade for Questions feature service API."""

from __future__ import annotations

from features.questions.level_service import (
    continue_level,
    go_home,
    open_level_entry,
    show_level_completion,
    show_levels_or_empty,
    start_level_from_beginning,
)
from features.questions.question_service import (
    QuestionActionResult,
    finish_current_question,
    go_to_next_question,
    go_to_previous_question,
    show_question_view,
)

__all__ = [
    "QuestionActionResult",
    "show_levels_or_empty",
    "open_level_entry",
    "continue_level",
    "start_level_from_beginning",
    "show_level_completion",
    "go_home",
    "show_question_view",
    "go_to_previous_question",
    "go_to_next_question",
    "finish_current_question",
]
