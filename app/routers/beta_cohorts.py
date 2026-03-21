from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.beta_cohort_schema import (
    BetaCohortCreate,
    BetaCohortDetailResponse,
    BetaCohortMembershipCreate,
    BetaCohortMembershipRead,
    BetaCohortMembershipUpdate,
    BetaCohortRead,
    BetaCohortUpdate,
    UserBetaAccessResponse,
)
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.beta_cohort_service import (
    add_user_to_cohort,
    get_beta_cohort_or_404,
    get_beta_membership_or_404,
    get_cohort_detail,
    get_user_beta_cohorts,
    list_cohort_memberships,
    list_cohorts,
    create_beta_cohort,
    update_beta_cohort,
    update_membership,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/beta", tags=["beta"])
admin_router = APIRouter(prefix="/admin/beta-cohorts", tags=["beta-admin"])
membership_router = APIRouter(prefix="/admin/beta-cohort-memberships", tags=["beta-admin"])


@admin_router.get("", response_model=list[BetaCohortRead], summary="List beta cohorts")
def get_beta_cohorts(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[BetaCohortRead]:
    return list_cohorts(session)


@admin_router.get("/{cohort_id}", response_model=BetaCohortDetailResponse, summary="Get beta cohort detail")
def get_beta_cohort(
    cohort_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> BetaCohortDetailResponse:
    cohort, memberships = get_cohort_detail(session, cohort_id=cohort_id)
    return BetaCohortDetailResponse(
        cohort=BetaCohortRead.model_validate(cohort),
        memberships=[BetaCohortMembershipRead.model_validate(item) for item in memberships],
    )


@admin_router.get("/{cohort_id}/members", response_model=list[BetaCohortMembershipRead], summary="List beta cohort members")
def get_beta_cohort_members(
    cohort_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[BetaCohortMembershipRead]:
    get_beta_cohort_or_404(session, cohort_id=cohort_id)
    return list_cohort_memberships(session, cohort_id=cohort_id)


@admin_router.post("", response_model=BetaCohortRead, status_code=status.HTTP_201_CREATED, summary="Create beta cohort")
def post_beta_cohort(
    payload: BetaCohortCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> BetaCohortRead:
    cohort = create_beta_cohort(
        session,
        key=payload.key,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        feature_flag_keys=payload.feature_flag_keys,
        notes=payload.notes,
        created_by_user_id=current_user.id,
    )
    create_audit_log(
        session,
        action_type="beta_cohort_created",
        entity_type="beta_cohort",
        entity_id=str(cohort.id),
        summary=f"Created beta cohort '{cohort.key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(mode="json"),
    )
    return cohort


@admin_router.patch("/{cohort_id}", response_model=BetaCohortRead, summary="Update beta cohort")
def patch_beta_cohort(
    cohort_id: int,
    payload: BetaCohortUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> BetaCohortRead:
    cohort = get_beta_cohort_or_404(session, cohort_id=cohort_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_beta_cohort(
        session,
        cohort=cohort,
        key=update_data.get("key"),
        name=update_data.get("name"),
        description=update_data.get("description"),
        is_active=update_data.get("is_active"),
        feature_flag_keys=update_data.get("feature_flag_keys"),
        notes=update_data.get("notes"),
        description_provided="description" in update_data,
        feature_flag_keys_provided="feature_flag_keys" in update_data,
        notes_provided="notes" in update_data,
    )
    create_audit_log(
        session,
        action_type="beta_cohort_updated",
        entity_type="beta_cohort",
        entity_id=str(updated.id),
        summary=f"Updated beta cohort '{updated.key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@admin_router.post("/{cohort_id}/members", response_model=BetaCohortMembershipRead, status_code=status.HTTP_201_CREATED, summary="Add user to beta cohort")
def post_beta_cohort_member(
    cohort_id: int,
    payload: BetaCohortMembershipCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> BetaCohortMembershipRead:
    cohort = get_beta_cohort_or_404(session, cohort_id=cohort_id)
    membership = add_user_to_cohort(
        session,
        cohort=cohort,
        user_id=payload.user_id,
        source=payload.source,
        invited_by_user_id=current_user.id,
        is_active=payload.is_active,
    )
    track_event_safe(
        session,
        event_name="beta_cohort_membership_added",
        user=current_user,
        metadata={"cohort_id": cohort.id, "membership_id": membership.id, "member_user_id": membership.user_id},
    )
    create_audit_log(
        session,
        action_type="beta_membership_added",
        entity_type="beta_cohort_membership",
        entity_id=str(membership.id),
        summary=f"Added user {membership.user_id} to beta cohort '{cohort.key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"cohort_id": cohort.id, "user_id": membership.user_id, "source": membership.source, "is_active": membership.is_active},
    )
    return membership


@membership_router.patch("/{membership_id}", response_model=BetaCohortMembershipRead, summary="Update beta cohort membership")
def patch_beta_membership(
    membership_id: int,
    payload: BetaCohortMembershipUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> BetaCohortMembershipRead:
    membership = get_beta_membership_or_404(session, membership_id=membership_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_membership(session, membership=membership, is_active=update_data.get("is_active"))
    track_event_safe(
        session,
        event_name="beta_cohort_membership_removed" if updated.is_active is False else "beta_cohort_membership_added",
        user=current_user,
        metadata={"membership_id": updated.id, "member_user_id": updated.user_id, "is_active": updated.is_active},
    )
    create_audit_log(
        session,
        action_type="beta_membership_updated",
        entity_type="beta_cohort_membership",
        entity_id=str(updated.id),
        summary=f"Updated beta cohort membership {updated.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@router.get("/me", response_model=UserBetaAccessResponse, summary="Get current user's beta access")
def get_my_beta_access(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserBetaAccessResponse:
    cohorts = get_user_beta_cohorts(session, user_id=current_user.id)
    track_event_safe(
        session,
        event_name="beta_access_checked",
        user=current_user,
        metadata={"cohort_count": len(cohorts)},
    )
    return UserBetaAccessResponse(
        user_id=current_user.id,
        cohorts=[BetaCohortRead.model_validate(item) for item in cohorts],
        cohort_keys=[item.key for item in cohorts],
    )
