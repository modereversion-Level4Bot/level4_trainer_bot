"""Session/state helpers for routes service."""

from __future__ import annotations


_PHASE_SCENARIO = "scenario"
_PHASE_NEWS = "news"
_PHASE_QUESTIONS = "questions"
_ENTRY_MODE_FULL = "full"
_ENTRY_MODE_FREE_NEWS = "free_news"
_ENTRY_MODE_FREE_QUESTIONS = "free_questions"


def _is_state_active_for_route(
    state: dict[str, object] | None,
    *,
    route_id: int,
    allowed_phases: set[str] | None = None,
) -> bool:
    if state is None:
        return False
    if int(state.get("route_id") or 0) != route_id:
        return False
    if int(state.get("is_active_session") or 0) != 1:
        return False
    phase = str(state.get("phase") or "").strip().lower()
    if allowed_phases is None:
        return True
    return phase in allowed_phases


def _state_phase(state: dict[str, object] | None) -> str:
    return str((state or {}).get("phase") or "").strip().lower()


def _state_entry_mode(state: dict[str, object] | None) -> str:
    return str((state or {}).get("entry_mode") or "").strip().lower()


def _is_full_entry_mode(state: dict[str, object] | None) -> bool:
    return _state_entry_mode(state) == _ENTRY_MODE_FULL
