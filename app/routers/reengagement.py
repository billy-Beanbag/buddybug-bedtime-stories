from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.reengagement_schema import (
    ReengagementDashboardResponse,
    ReengagementSuggestionRead,
    ReengagementSuggestionUpdate,
    UserEngagementStateRead,
)
from app.services.reengagement_service import (
    dismiss_reengagement_suggestion,
    get_reengagement_dashboard,
    get_reengagement_suggestion_or_404,
    list_engagement_states_for_admin,
    list_reengagement_suggestions_for_admin,
    list_reengagement_suggestions_for_user,
    rebuild_user_engagement_state,
    generate_reengagement_suggestions,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/reengagement", tags=["reengagement"])
admin_router = APIRouter(prefix="/admin/reengagement", tags=["admin-reengagement"])


@router.get("/me", response_model=ReengagementDashboardResponse, summary="Get my reengagement dashboard")
def get_my_reengagement_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReengagementDashboardResponse:
    state, suggestions = get_reengagement_dashboard(session, user=current_user)
    return ReengagementDashboardResponse(engagement_state=state, suggestions=suggestions)


@router.get("/me/state", response_model=UserEngagementStateRead, summary="Get my engagement state")
def get_my_engagement_state(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserEngagementStateRead:
    state, _suggestions = get_reengagement_dashboard(session, user=current_user)
    return state


@router.get(
    "/me/suggestions",
    response_model=list[ReengagementSuggestionRead],
    summary="List my current reengagement suggestions",
)
def get_my_reengagement_suggestions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[ReengagementSuggestionRead]:
    _state, _suggestions = get_reengagement_dashboard(session, user=current_user)
    return list_reengagement_suggestions_for_user(session, user_id=current_user.id, include_dismissed=False)


@router.patch(
    "/me/suggestions/{suggestion_id}",
    response_model=ReengagementSuggestionRead,
    summary="Update one reengagement suggestion",
)
def patch_my_reengagement_suggestion(
    suggestion_id: int,
    payload: ReengagementSuggestionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReengagementSuggestionRead:
    suggestion = get_reengagement_suggestion_or_404(session, suggestion_id=suggestion_id)
    if suggestion.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reengagement suggestion not found")
    return dismiss_reengagement_suggestion(
        session,
        suggestion=suggestion,
        is_dismissed=payload.is_dismissed if payload.is_dismissed is not None else suggestion.is_dismissed,
    )


@router.post("/me/rebuild", response_model=ReengagementDashboardResponse, summary="Rebuild my reengagement state")
def rebuild_my_reengagement_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReengagementDashboardResponse:
    state = rebuild_user_engagement_state(session, user=current_user)
    suggestions = generate_reengagement_suggestions(session, user=current_user, engagement_state=state)
    return ReengagementDashboardResponse(engagement_state=state, suggestions=suggestions)


@admin_router.get("/states", response_model=list[UserEngagementStateRead], summary="List engagement states")
def list_reengagement_states_admin(
    state_key: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[UserEngagementStateRead]:
    return list_engagement_states_for_admin(session, state_key=state_key, limit=limit)


@admin_router.get(
    "/suggestions",
    response_model=list[ReengagementSuggestionRead],
    summary="List reengagement suggestions",
)
def list_reengagement_suggestions_admin(
    suggestion_type: str | None = Query(default=None),
    state_key: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[ReengagementSuggestionRead]:
    return list_reengagement_suggestions_for_admin(
        session,
        suggestion_type=suggestion_type,
        state_key=state_key,
        limit=limit,
    )


@admin_router.post(
    "/users/{user_id}/rebuild",
    response_model=ReengagementDashboardResponse,
    summary="Rebuild one user's reengagement dashboard",
)
def rebuild_reengagement_for_user(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> ReengagementDashboardResponse:
    target_user = session.get(User, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    state = rebuild_user_engagement_state(session, user=target_user)
    suggestions = generate_reengagement_suggestions(session, user=target_user, engagement_state=state)
    return ReengagementDashboardResponse(engagement_state=state, suggestions=suggestions)
