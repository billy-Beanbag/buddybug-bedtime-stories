from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import OnboardingState
from app.services.review_service import utc_now

ONBOARDING_STEPS = {"welcome", "child_setup", "preferences", "bedtime_mode", "first_story", "done"}
STEP_ROUTE_MAP = {
    "welcome": "/onboarding",
    "child_setup": "/onboarding/child",
    "preferences": "/onboarding/preferences",
    "bedtime_mode": "/onboarding/bedtime",
    "first_story": "/onboarding/first-story",
    "done": "/library",
}


def validate_onboarding_step(step: str) -> str:
    if step not in ONBOARDING_STEPS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid onboarding step")
    return step


def get_or_create_onboarding_state(session: Session, *, user_id: int) -> OnboardingState:
    statement = select(OnboardingState).where(OnboardingState.user_id == user_id)
    existing = session.exec(statement).first()
    if existing is not None:
        return existing
    state = OnboardingState(user_id=user_id)
    session.add(state)
    session.commit()
    session.refresh(state)
    return state


def update_onboarding_state(
    session: Session,
    *,
    state: OnboardingState,
    current_step: str | None = None,
    completed: bool | None = None,
    skipped: bool | None = None,
    child_profile_created: bool | None = None,
    preferred_age_band: str | None = None,
    preferred_language: str | None = None,
    bedtime_mode_reviewed: bool | None = None,
    first_story_opened: bool | None = None,
    completed_at: datetime | None = None,
) -> OnboardingState:
    if current_step is not None:
        state.current_step = validate_onboarding_step(current_step)
    if completed is not None:
        state.completed = completed
    if skipped is not None:
        state.skipped = skipped
    if child_profile_created is not None:
        state.child_profile_created = child_profile_created
    if preferred_age_band is not None:
        state.preferred_age_band = preferred_age_band
    if preferred_language is not None:
        state.preferred_language = preferred_language
    if bedtime_mode_reviewed is not None:
        state.bedtime_mode_reviewed = bedtime_mode_reviewed
    if first_story_opened is not None:
        state.first_story_opened = first_story_opened
    if completed_at is not None:
        state.completed_at = completed_at

    if state.completed:
        state.current_step = "done"
        state.completed_at = state.completed_at or utc_now()
    else:
        if state.current_step == "done":
            state.current_step = "welcome"
        if state.skipped:
            state.skipped = False
        if state.completed_at is not None:
            state.completed_at = None

    state.updated_at = utc_now()
    session.add(state)
    session.commit()
    session.refresh(state)
    return state


def advance_onboarding(
    session: Session,
    *,
    state: OnboardingState,
    next_step: str | None = None,
    preferred_age_band: str | None = None,
    preferred_language: str | None = None,
    child_profile_created: bool | None = None,
    bedtime_mode_reviewed: bool | None = None,
    first_story_opened: bool | None = None,
) -> OnboardingState:
    target_step = next_step
    if first_story_opened:
        return complete_onboarding(
            session,
            state=update_onboarding_state(
                session,
                state=state,
                child_profile_created=child_profile_created,
                preferred_age_band=preferred_age_band,
                preferred_language=preferred_language,
                bedtime_mode_reviewed=bedtime_mode_reviewed,
                first_story_opened=True,
            ),
        )
    if target_step is None:
        target_step = _infer_next_step(
            state=state,
            child_profile_created=child_profile_created,
            preferred_age_band=preferred_age_band,
            preferred_language=preferred_language,
            bedtime_mode_reviewed=bedtime_mode_reviewed,
        )
    return update_onboarding_state(
        session,
        state=state,
        current_step=target_step,
        child_profile_created=child_profile_created,
        preferred_age_band=preferred_age_band,
        preferred_language=preferred_language,
        bedtime_mode_reviewed=bedtime_mode_reviewed,
        first_story_opened=first_story_opened,
    )


def skip_onboarding(session: Session, *, state: OnboardingState) -> OnboardingState:
    return update_onboarding_state(
        session,
        state=state,
        current_step="done",
        skipped=True,
        completed=True,
        completed_at=utc_now(),
    )


def complete_onboarding(session: Session, *, state: OnboardingState) -> OnboardingState:
    return update_onboarding_state(
        session,
        state=state,
        current_step="done",
        completed=True,
        completed_at=utc_now(),
    )


def get_recommended_next_route(state: OnboardingState) -> str:
    if state.completed or state.skipped:
        return "/library"
    if state.current_step == "done":
        return "/library"
    return STEP_ROUTE_MAP.get(state.current_step, "/onboarding")


def _infer_next_step(
    *,
    state: OnboardingState,
    child_profile_created: bool | None = None,
    preferred_age_band: str | None = None,
    preferred_language: str | None = None,
    bedtime_mode_reviewed: bool | None = None,
) -> str:
    if not (child_profile_created if child_profile_created is not None else state.child_profile_created):
        return "child_setup"
    if not ((preferred_age_band or state.preferred_age_band) and (preferred_language or state.preferred_language)):
        return "preferences"
    if not (bedtime_mode_reviewed if bedtime_mode_reviewed is not None else state.bedtime_mode_reviewed):
        return "bedtime_mode"
    if not state.first_story_opened:
        return "first_story"
    return "done"
