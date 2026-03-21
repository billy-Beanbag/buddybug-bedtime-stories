from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.onboarding_schema import (
    OnboardingAdvanceRequest,
    OnboardingStartResponse,
    OnboardingStateRead,
    OnboardingStateUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.onboarding_service import (
    advance_onboarding,
    complete_onboarding,
    get_or_create_onboarding_state,
    get_recommended_next_route,
    skip_onboarding,
    update_onboarding_state,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/me", response_model=OnboardingStateRead, summary="Get the current user's onboarding state")
def get_my_onboarding_state(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OnboardingStateRead:
    return get_or_create_onboarding_state(session, user_id=current_user.id)


@router.patch("/me", response_model=OnboardingStateRead, summary="Update onboarding state")
def patch_my_onboarding_state(
    payload: OnboardingStateUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OnboardingStateRead:
    state = get_or_create_onboarding_state(session, user_id=current_user.id)
    return update_onboarding_state(session, state=state, **payload.model_dump(exclude_unset=True))


@router.post("/me/advance", response_model=OnboardingStartResponse, summary="Advance onboarding flow")
def advance_my_onboarding(
    payload: OnboardingAdvanceRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OnboardingStartResponse:
    state = get_or_create_onboarding_state(session, user_id=current_user.id)
    updated = advance_onboarding(session, state=state, **payload.model_dump(exclude_unset=True))
    return OnboardingStartResponse(
        state=OnboardingStateRead.model_validate(updated),
        recommended_next_route=get_recommended_next_route(updated),
    )


@router.post("/me/skip", response_model=OnboardingStateRead, summary="Skip onboarding")
def skip_my_onboarding(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OnboardingStateRead:
    state = get_or_create_onboarding_state(session, user_id=current_user.id)
    skipped = skip_onboarding(session, state=state)
    return skipped


@router.post("/me/complete", response_model=OnboardingStateRead, summary="Complete onboarding")
def complete_my_onboarding(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OnboardingStateRead:
    state = get_or_create_onboarding_state(session, user_id=current_user.id)
    completed = complete_onboarding(session, state=state)
    create_audit_log(
        session,
        action_type="onboarding_completed",
        entity_type="onboarding_state",
        entity_id=str(completed.id),
        summary=f"Completed onboarding for user {current_user.email}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"user_id": current_user.id},
    )
    return completed
