"""Routes repository compatibility facade."""

from __future__ import annotations

from db.repositories.routes_import_repo import (
    deactivate_route_news_absent,
    deactivate_route_question_blocks_absent,
    deactivate_route_questions_absent,
    deactivate_route_questions_absent_blocks,
    deactivate_route_steps_absent,
    deactivate_routes_absent,
    get_question_block_id,
    get_route_id_by_code,
    upsert_route,
    upsert_route_news,
    upsert_route_question,
    upsert_route_question_block,
    upsert_route_step,
)
from db.repositories.routes_media_repo import (
    list_active_route_briefing_image_assets,
    list_active_route_news_audio_assets,
    list_active_route_news_image_assets,
    list_active_route_question_image_assets,
    list_active_route_step_audio_assets,
    list_active_route_step_image_assets,
)
from db.repositories.routes_progress_repo import (
    count_completed_routes,
    mark_route_completed,
)
from db.repositories.routes_repo_common import (
    _ALLOWED_STEP_TYPES,
    _COMPLETED_ROUTE_STATUSES,
    _normalize_int,
    _normalize_is_active,
    _normalize_positive_int,
    _normalize_step_type,
    _optional_text,
    _required_text,
)
from db.repositories.routes_runtime_repo import (
    count_active_news_for_route,
    count_active_question_blocks_with_questions,
    count_active_routes,
    count_questions_in_block,
    get_active_steps_for_route,
    get_next_active_step_number,
    get_next_question_number,
    get_previous_active_step_number,
    get_previous_question_number,
    get_question_block_by_id,
    get_route_by_id,
    get_route_news_by_id,
    get_route_question,
    get_route_step,
    list_active_news_for_route,
    list_active_news_for_route_paginated,
    list_active_question_blocks,
    list_active_question_blocks_with_question_counts,
    list_active_questions_for_block,
    list_active_routes,
)
from db.repositories.routes_state_repo import (
    clear_route_user_state,
    deactivate_active_route_sessions,
    get_route_user_state,
    update_route_news_transcript_state,
    update_route_question_state,
    update_route_step_state,
    upsert_route_news_state,
    upsert_route_questions_state,
    upsert_route_user_state,
)
