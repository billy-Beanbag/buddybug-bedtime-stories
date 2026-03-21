from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.reading_plan_schema import (
    ReadingPlanCreate,
    ReadingPlanDetailResponse,
    ReadingPlanRead,
    ReadingPlanSessionRead,
    ReadingPlanSuggestionResponse,
    ReadingPlanUpdate,
)
from app.services.analytics_service import track_event_safe
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.reading_plan_service import (
    archive_reading_plan,
    create_reading_plan,
    get_reading_plan_detail,
    generate_upcoming_sessions,
    list_reading_plans_for_user,
    mark_plan_session_completed,
    suggest_books_for_plan,
    update_reading_plan,
    validate_plan_access,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/reading-plans", tags=["reading-plans"])


@router.get("/me", response_model=list[ReadingPlanRead], summary="List current user reading plans")
def list_my_reading_plans(
    status_value: str | None = Query(default=None, alias="status"),
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[ReadingPlanRead]:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    return list_reading_plans_for_user(
        session,
        user_id=current_user.id,
        status_value=status_value,
        child_profile_id=child_profile_id,
    )


@router.get("/me/{plan_id}", response_model=ReadingPlanDetailResponse, summary="Get one reading plan with upcoming sessions")
def get_my_reading_plan(
    plan_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadingPlanDetailResponse:
    plan, upcoming_sessions = get_reading_plan_detail(session, user=current_user, plan_id=plan_id)
    return ReadingPlanDetailResponse(plan=plan, upcoming_sessions=upcoming_sessions)


@router.post("/me", response_model=ReadingPlanRead, summary="Create a reading plan")
def create_my_reading_plan(
    payload: ReadingPlanCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadingPlanRead:
    plan = create_reading_plan(session, user=current_user, **payload.model_dump())
    track_event_safe(
        session,
        event_name="reading_plan_created",
        user=current_user,
        child_profile_id=plan.child_profile_id,
        metadata={"plan_id": plan.id, "plan_type": plan.plan_type, "status": plan.status},
    )
    return plan


@router.patch("/me/{plan_id}", response_model=ReadingPlanRead, summary="Update a reading plan")
def patch_my_reading_plan(
    plan_id: int,
    payload: ReadingPlanUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadingPlanRead:
    plan = validate_plan_access(session, user_id=current_user.id, plan_id=plan_id)
    updated = update_reading_plan(session, plan=plan, user=current_user, changes=payload.model_dump(exclude_unset=True))
    track_event_safe(
        session,
        event_name="reading_plan_updated",
        user=current_user,
        child_profile_id=updated.child_profile_id,
        metadata={"plan_id": updated.id, "plan_type": updated.plan_type, "status": updated.status},
    )
    return updated


@router.delete("/me/{plan_id}", response_model=ReadingPlanRead, summary="Archive a reading plan")
def delete_my_reading_plan(
    plan_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadingPlanRead:
    archived = archive_reading_plan(session, user=current_user, plan_id=plan_id)
    return archived


@router.get("/me/{plan_id}/suggestions", response_model=ReadingPlanSuggestionResponse, summary="Get suggested books for a reading plan")
def get_my_reading_plan_suggestions(
    plan_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadingPlanSuggestionResponse:
    plan = validate_plan_access(session, user_id=current_user.id, plan_id=plan_id)
    suggestions = suggest_books_for_plan(session, user=current_user, plan=plan)
    track_event_safe(
        session,
        event_name="reading_plan_suggestions_viewed",
        user=current_user,
        child_profile_id=plan.child_profile_id,
        metadata={"plan_id": plan.id, "suggestion_count": len(suggestions)},
    )
    return ReadingPlanSuggestionResponse(plan=plan, suggested_books=suggestions)


@router.post("/me/{plan_id}/sessions/{session_id}/complete", response_model=ReadingPlanSessionRead, summary="Mark a reading plan session completed")
def complete_my_reading_plan_session(
    plan_id: int,
    session_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadingPlanSessionRead:
    completed_session = mark_plan_session_completed(session, user=current_user, plan_id=plan_id, session_id=session_id)
    plan = validate_plan_access(session, user_id=current_user.id, plan_id=plan_id)
    track_event_safe(
        session,
        event_name="reading_plan_session_completed",
        user=current_user,
        child_profile_id=plan.child_profile_id,
        metadata={"plan_id": plan.id, "session_id": completed_session.id, "scheduled_date": str(completed_session.scheduled_date)},
    )
    return completed_session


@router.post("/me/{plan_id}/sessions/generate", response_model=ReadingPlanDetailResponse, summary="Generate upcoming reading plan sessions")
def generate_my_reading_plan_sessions(
    plan_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadingPlanDetailResponse:
    plan = validate_plan_access(session, user_id=current_user.id, plan_id=plan_id)
    upcoming_sessions = generate_upcoming_sessions(session, user=current_user, plan=plan)
    return ReadingPlanDetailResponse(plan=plan, upcoming_sessions=upcoming_sessions)
