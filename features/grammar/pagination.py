"""Pagination helpers for grammar feature."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar


GRAMMAR_TOPICS_PAGE_SIZE = 5
TopicItem = TypeVar("TopicItem")


@dataclass(slots=True)
class TopicNavigationContext:
    current_page: int
    previous_topic_number: int | None
    previous_topic_page: int | None
    next_topic_number: int | None
    next_topic_page: int | None


def _to_positive_int(value: object, fallback: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def _to_non_negative_int(value: object, fallback: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed >= 0 else fallback


def _paginate_items(
    items: list[TopicItem],
    *,
    page: int,
    page_size: int,
) -> tuple[list[TopicItem], int, int]:
    if not items:
        return [], 1, 1

    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    safe_page = max(1, min(page, total_pages))
    start_idx = (safe_page - 1) * page_size
    end_idx = start_idx + page_size
    return items[start_idx:end_idx], safe_page, total_pages


def _build_topic_navigation_context(
    topics: list[dict[str, object]],
    *,
    topic_number: int,
) -> TopicNavigationContext:
    topic_numbers = [
        _to_positive_int(topic.get("topic_number"), fallback=0)
        for topic in topics
        if _to_positive_int(topic.get("topic_number"), fallback=0) > 0
    ]
    if not topic_numbers:
        return TopicNavigationContext(
            current_page=1,
            previous_topic_number=None,
            previous_topic_page=None,
            next_topic_number=None,
            next_topic_page=None,
        )

    try:
        current_index = topic_numbers.index(topic_number)
    except ValueError:
        return TopicNavigationContext(
            current_page=1,
            previous_topic_number=None,
            previous_topic_page=None,
            next_topic_number=None,
            next_topic_page=None,
        )

    previous_topic_number: int | None = None
    previous_topic_page: int | None = None
    if current_index > 0:
        previous_topic_number = topic_numbers[current_index - 1]
        previous_topic_page = ((current_index - 1) // GRAMMAR_TOPICS_PAGE_SIZE) + 1

    next_topic_number: int | None = None
    next_topic_page: int | None = None
    if current_index < (len(topic_numbers) - 1):
        next_topic_number = topic_numbers[current_index + 1]
        next_topic_page = ((current_index + 1) // GRAMMAR_TOPICS_PAGE_SIZE) + 1

    return TopicNavigationContext(
        current_page=(current_index // GRAMMAR_TOPICS_PAGE_SIZE) + 1,
        previous_topic_number=previous_topic_number,
        previous_topic_page=previous_topic_page,
        next_topic_number=next_topic_number,
        next_topic_page=next_topic_page,
    )
