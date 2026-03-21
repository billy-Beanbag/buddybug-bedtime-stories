from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.achievement_schema import (
    AchievementDashboardResponse,
    AchievementDefinitionRead,
    EarnedAchievementRead,
)
from app.services.achievement_service import (
    get_achievement_dashboard,
    get_achievement_definitions,
    get_earned_achievements_for_user,
    rebuild_achievements_for_user,
)
from app.services.analytics_service import track_event_safe
from app.services.child_profile_service import validate_child_profile_ownership
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/achievements", tags=["achievements"])
admin_router = APIRouter(prefix="/admin/achievements", tags=["admin-achievements"])


@router.get("/me", response_model=AchievementDashboardResponse, summary="Get my achievement dashboard")
def get_my_achievement_dashboard(
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> AchievementDashboardResponse:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    dashboard = get_achievement_dashboard(session, user=current_user, child_profile_id=child_profile_id)
    track_event_safe(
        session,
        event_name="achievement_dashboard_viewed",
        user=current_user,
        child_profile_id=child_profile_id,
        metadata={
            "earned_count": len(dashboard.earned_achievements),
            "current_streak": dashboard.current_streak,
            "longest_streak": dashboard.longest_streak,
        },
    )
    return dashboard


@router.get("/me/list", response_model=list[EarnedAchievementRead], summary="List my earned achievements")
def list_my_earned_achievements(
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[EarnedAchievementRead]:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    return get_earned_achievements_for_user(
        session,
        user_id=current_user.id,
        child_profile_id=child_profile_id,
    )


@router.post("/me/rebuild", response_model=AchievementDashboardResponse, summary="Rebuild my achievements")
def rebuild_my_achievements(
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> AchievementDashboardResponse:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    return rebuild_achievements_for_user(session, user=current_user, child_profile_id=child_profile_id)


@admin_router.get("/definitions", response_model=list[AchievementDefinitionRead], summary="List achievement definitions")
def list_admin_achievement_definitions(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[AchievementDefinitionRead]:
    return get_achievement_definitions(session, active_only=False)
