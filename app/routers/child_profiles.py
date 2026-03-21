from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import ChildReadingProfile, User
from app.schemas.child_profile_schema import (
    ChildProfileCreate,
    ChildProfileRead,
    ChildProfileSelectionResponse,
    ChildProfileUpdate,
    ChildReadingProfileRead,
)
from app.services.audit_service import create_audit_log
from app.services.child_profile_service import (
    create_child_profile,
    deactivate_child_profile,
    get_child_profile_for_user,
    get_child_profiles_for_user,
    get_or_create_child_reading_profile,
    rebuild_child_reading_profile,
    update_child_profile,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/child-profiles", tags=["child-profiles"])


@router.get("", response_model=list[ChildProfileRead], summary="List child profiles for the current user")
def list_child_profiles(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list:
    return get_child_profiles_for_user(session, user_id=current_user.id)


@router.get("/{child_profile_id}", response_model=ChildProfileRead, summary="Get one child profile")
def get_child_profile(
    child_profile_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    return get_child_profile_for_user(session, user_id=current_user.id, child_profile_id=child_profile_id)


@router.post("", response_model=ChildProfileSelectionResponse, status_code=status.HTTP_201_CREATED, summary="Create a child profile")
def create_my_child_profile(
    payload: ChildProfileCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ChildProfileSelectionResponse:
    child_profile, reading_profile = create_child_profile(
        session,
        user_id=current_user.id,
        display_name=payload.display_name,
        birth_year=payload.birth_year,
        age_band=payload.age_band,
        language=payload.language,
        content_lane_key=payload.content_lane_key,
        is_active=payload.is_active,
    )
    create_audit_log(
        session,
        action_type="child_profile_created",
        entity_type="child_profile",
        entity_id=str(child_profile.id),
        summary=f"Created child profile '{child_profile.display_name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"age_band": child_profile.age_band, "language": child_profile.language},
    )
    return ChildProfileSelectionResponse(
        child_profile=ChildProfileRead.model_validate(child_profile),
        reading_profile=ChildReadingProfileRead.model_validate(reading_profile),
    )


@router.patch("/{child_profile_id}", response_model=ChildProfileRead, summary="Update a child profile")
def update_my_child_profile(
    child_profile_id: int,
    payload: ChildProfileUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    child_profile = get_child_profile_for_user(session, user_id=current_user.id, child_profile_id=child_profile_id)
    updated = update_child_profile(
        session,
        child_profile=child_profile,
        display_name=payload.display_name,
        birth_year=payload.birth_year,
        age_band=payload.age_band,
        language=payload.language,
        content_lane_key=payload.content_lane_key,
        is_active=payload.is_active,
    )
    create_audit_log(
        session,
        action_type="child_profile_updated",
        entity_type="child_profile",
        entity_id=str(updated.id),
        summary=f"Updated child profile '{updated.display_name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"age_band": updated.age_band, "language": updated.language, "is_active": updated.is_active},
    )
    return updated


@router.post("/{child_profile_id}/deactivate", response_model=ChildProfileRead, summary="Deactivate a child profile")
def deactivate_my_child_profile(
    child_profile_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    child_profile = get_child_profile_for_user(session, user_id=current_user.id, child_profile_id=child_profile_id)
    deactivated = deactivate_child_profile(session, child_profile=child_profile)
    create_audit_log(
        session,
        action_type="child_profile_deactivated",
        entity_type="child_profile",
        entity_id=str(deactivated.id),
        summary=f"Deactivated child profile '{deactivated.display_name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"age_band": deactivated.age_band},
    )
    return deactivated


@router.get(
    "/{child_profile_id}/reading-profile",
    response_model=ChildReadingProfileRead,
    summary="Get the reading profile for one child profile",
)
def get_child_reading_profile(
    child_profile_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ChildReadingProfile:
    child_profile = get_child_profile_for_user(session, user_id=current_user.id, child_profile_id=child_profile_id)
    return get_or_create_child_reading_profile(session, child_profile_id=child_profile.id)


@router.post(
    "/{child_profile_id}/reading-profile/rebuild",
    response_model=ChildReadingProfileRead,
    summary="Rebuild the reading profile for one child profile",
)
def rebuild_my_child_reading_profile(
    child_profile_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ChildReadingProfile:
    child_profile = get_child_profile_for_user(session, user_id=current_user.id, child_profile_id=child_profile_id)
    profile = rebuild_child_reading_profile(session, child_profile=child_profile)
    create_audit_log(
        session,
        action_type="child_reading_profile_rebuilt",
        entity_type="child_profile",
        entity_id=str(child_profile.id),
        summary=f"Rebuilt child reading profile for '{child_profile.display_name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"child_profile_id": child_profile.id},
    )
    return profile
