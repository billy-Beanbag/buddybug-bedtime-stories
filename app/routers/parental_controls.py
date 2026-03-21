from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.parental_controls_schema import (
    ChildControlOverrideRead,
    ChildControlOverrideUpdate,
    ParentalControlSettingsRead,
    ParentalControlSettingsUpdate,
    ResolvedParentalControlsResponse,
)
from app.services.audit_service import create_audit_log
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.parental_controls_service import (
    get_child_override,
    get_or_create_child_override_placeholder,
    get_or_create_parental_settings,
    resolve_parental_controls,
    upsert_child_override,
    update_parental_settings,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/parental-controls", tags=["parental-controls"])


@router.get("/me", response_model=ParentalControlSettingsRead, summary="Get account-level parental controls")
def get_my_parental_controls(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ParentalControlSettingsRead:
    return get_or_create_parental_settings(session, user_id=current_user.id)


@router.patch("/me", response_model=ParentalControlSettingsRead, summary="Update account-level parental controls")
def patch_my_parental_controls(
    payload: ParentalControlSettingsUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ParentalControlSettingsRead:
    settings = get_or_create_parental_settings(session, user_id=current_user.id)
    updated = update_parental_settings(session, settings=settings, **payload.model_dump(exclude_unset=True))
    create_audit_log(
        session,
        action_type="parental_controls_updated",
        entity_type="parental_control_settings",
        entity_id=str(updated.id),
        summary=f"Updated parental controls for user {current_user.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@router.get(
    "/children/{child_profile_id}",
    response_model=ChildControlOverrideRead,
    summary="Get one child control override or empty inherited settings object",
)
def get_my_child_control_override(
    child_profile_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ChildControlOverrideRead:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    override = get_child_override(session, child_profile_id=child_profile_id)
    if override is None:
        return ChildControlOverrideRead.model_validate(get_or_create_child_override_placeholder(child_profile_id=child_profile_id))
    return override


@router.patch(
    "/children/{child_profile_id}",
    response_model=ChildControlOverrideRead,
    summary="Create or update one child control override",
)
def patch_my_child_control_override(
    child_profile_id: int,
    payload: ChildControlOverrideUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ChildControlOverrideRead:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    override = upsert_child_override(
        session,
        child_profile_id=child_profile_id,
        **payload.model_dump(exclude_unset=True),
    )
    create_audit_log(
        session,
        action_type="child_control_override_updated",
        entity_type="child_control_override",
        entity_id=str(override.id),
        summary=f"Updated parental override for child profile {child_profile_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return override


@router.get("/resolved", response_model=ResolvedParentalControlsResponse, summary="Get resolved parental controls")
def get_resolved_parental_controls(
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ResolvedParentalControlsResponse:
    resolved = resolve_parental_controls(session, user=current_user, child_profile_id=child_profile_id)
    return ResolvedParentalControlsResponse(**resolved.__dict__)
