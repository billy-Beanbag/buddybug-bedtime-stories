from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.child_comfort_schema import ChildComfortProfileRead, ChildComfortProfileUpdate
from app.services.analytics_service import track_event_safe
from app.services.child_comfort_service import (
    get_child_comfort_profile_for_user,
    update_child_comfort_profile,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/child-comfort", tags=["child-comfort"])


@router.get(
    "/{child_profile_id}",
    response_model=ChildComfortProfileRead,
    summary="Get the comfort profile for one child profile",
)
def get_child_comfort(
    child_profile_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ChildComfortProfileRead:
    _child_profile, profile = get_child_comfort_profile_for_user(
        session,
        user_id=current_user.id,
        child_profile_id=child_profile_id,
    )
    return ChildComfortProfileRead.model_validate(profile)


@router.patch(
    "/{child_profile_id}",
    response_model=ChildComfortProfileRead,
    summary="Create or update the comfort profile for one child profile",
)
def patch_child_comfort(
    child_profile_id: int,
    payload: ChildComfortProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ChildComfortProfileRead:
    child_profile, profile = get_child_comfort_profile_for_user(
        session,
        user_id=current_user.id,
        child_profile_id=child_profile_id,
    )
    updated = update_child_comfort_profile(session, profile=profile, **payload.model_dump(exclude_unset=True))
    track_event_safe(
        session,
        event_name="child_comfort_profile_updated",
        user_id=current_user.id,
        child_profile_id=child_profile.id,
        metadata={
            "prefer_narration": updated.prefer_narration,
            "prefer_shorter_stories": updated.prefer_shorter_stories,
            "extra_calm_mode": updated.extra_calm_mode,
            "preferred_language": updated.preferred_language,
        },
    )
    return ChildComfortProfileRead.model_validate(updated)
