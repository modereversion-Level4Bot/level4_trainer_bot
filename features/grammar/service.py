"""Compatibility facade for grammar feature service API."""

from __future__ import annotations

from features.grammar.pagination import GRAMMAR_TOPICS_PAGE_SIZE
from features.grammar.topic_service import (
    show_extra_materials,
    show_grammar_list,
    show_topic,
    show_topic_details,
)
from features.grammar.training_service import (
    GRAMMAR_TRAINING_LIMIT,
    TrainingAnswerOutcome,
    create_new_training_session,
    process_answer,
    show_training_question,
    show_training_result,
)

__all__ = [
    "GRAMMAR_TOPICS_PAGE_SIZE",
    "GRAMMAR_TRAINING_LIMIT",
    "TrainingAnswerOutcome",
    "show_grammar_list",
    "show_extra_materials",
    "show_topic",
    "show_topic_details",
    "create_new_training_session",
    "show_training_question",
    "process_answer",
    "show_training_result",
]
