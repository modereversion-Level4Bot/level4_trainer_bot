"""Progress helpers for Questions feature."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from db.repositories.questions_progress_repo import (
    count_completed_questions_by_level,
    get_current_question_number,
    is_question_completed,
)
from db.repositories.questions_repo import list_active_questions_by_level


@dataclass(frozen=True, slots=True)
class LevelQuestionsContext:
    level: int
    questions: list[dict[str, object]]
    question_numbers: list[int]

    @property
    def total(self) -> int:
        return len(self.question_numbers)


@dataclass(frozen=True, slots=True)
class QuestionNavigationContext:
    level: int
    question_number: int
    index: int
    total: int
    has_prev: bool
    has_next: bool
    prev_question_number: int | None
    next_question_number: int | None
    question: dict[str, object]


def load_level_questions_context(
    conn: sqlite3.Connection,
    level: int,
) -> LevelQuestionsContext | None:
    questions = list_active_questions_by_level(conn, level)
    if not questions:
        return None
    question_numbers: list[int] = [int(row["question_number"]) for row in questions]
    return LevelQuestionsContext(
        level=int(level),
        questions=questions,
        question_numbers=question_numbers,
    )


def get_question_by_number(
    context: LevelQuestionsContext,
    question_number: int,
) -> dict[str, object] | None:
    normalized_question_number = int(question_number)
    for row in context.questions:
        if int(row["question_number"]) == normalized_question_number:
            return row
    return None


def resolve_question_navigation(
    context: LevelQuestionsContext,
    question_number: int,
) -> QuestionNavigationContext | None:
    normalized_question_number = int(question_number)
    question = get_question_by_number(context, normalized_question_number)
    if question is None:
        return None

    index0 = context.question_numbers.index(normalized_question_number)
    prev_question_number = (
        context.question_numbers[index0 - 1] if index0 > 0 else None
    )
    next_question_number = (
        context.question_numbers[index0 + 1]
        if index0 + 1 < len(context.question_numbers)
        else None
    )
    return QuestionNavigationContext(
        level=context.level,
        question_number=normalized_question_number,
        index=index0 + 1,
        total=context.total,
        has_prev=prev_question_number is not None,
        has_next=next_question_number is not None,
        prev_question_number=prev_question_number,
        next_question_number=next_question_number,
        question=question,
    )


def has_started_level(conn: sqlite3.Connection, user_id: int, level: int) -> bool:
    current_question_number = get_current_question_number(conn, user_id, level)
    if current_question_number is not None:
        return True
    return count_completed_questions_by_level(conn, user_id, level) > 0


def first_question_number(context: LevelQuestionsContext) -> int | None:
    if not context.question_numbers:
        return None
    return context.question_numbers[0]


def first_uncompleted_question_number(
    conn: sqlite3.Connection,
    user_id: int,
    context: LevelQuestionsContext,
) -> int | None:
    for question_number in context.question_numbers:
        if not is_question_completed(conn, user_id, context.level, question_number):
            return question_number
    return None


def resolve_continue_question_number(
    conn: sqlite3.Connection,
    user_id: int,
    context: LevelQuestionsContext,
) -> int | None:
    current_question_number = get_current_question_number(conn, user_id, context.level)
    if current_question_number is not None and current_question_number in context.question_numbers:
        return current_question_number

    unresolved = first_uncompleted_question_number(conn, user_id, context)
    if unresolved is not None:
        return unresolved

    return first_question_number(context)


def is_level_completed(
    conn: sqlite3.Connection,
    user_id: int,
    context: LevelQuestionsContext,
) -> bool:
    """Return True when all active questions in level are completed."""
    if context.total <= 0:
        return False
    for question_number in context.question_numbers:
        if not is_question_completed(conn, user_id, context.level, question_number):
            return False
    return True
