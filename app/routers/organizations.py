from fastapi import APIRouter, Depends, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.organization_schema import (
    OrganizationCreate,
    OrganizationDetailResponse,
    OrganizationMembershipCreate,
    OrganizationMembershipRead,
    OrganizationMembershipUpdate,
    OrganizationRead,
)
from app.services.audit_service import create_audit_log
from app.services.organization_service import (
    add_member,
    build_organization_detail_response,
    create_organization,
    get_membership_or_404,
    get_organization_detail_for_user,
    get_organization_or_404,
    list_members,
    remove_member,
    require_org_role,
    update_membership,
)
from app.utils.dependencies import get_current_active_user, get_current_org_admin_user, get_current_org_user

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me", response_model=OrganizationDetailResponse, summary="Get my organization")
def get_my_organization(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_org_user),
) -> OrganizationDetailResponse:
    organization, memberships = get_organization_detail_for_user(session, user=current_user)
    return OrganizationDetailResponse(**build_organization_detail_response(organization=organization, memberships=memberships))


@router.get("/me/members", response_model=list[OrganizationMembershipRead], summary="List members in my organization")
def get_my_organization_members(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_org_user),
) -> list[OrganizationMembershipRead]:
    organization, memberships = get_organization_detail_for_user(session, user=current_user)
    _ = organization
    return memberships


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED, summary="Create organization")
def create_my_organization(
    payload: OrganizationCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationRead:
    organization = create_organization(session, current_user=current_user, payload=payload)
    create_audit_log(
        session,
        action_type="organization_created",
        entity_type="organization",
        entity_id=str(organization.id),
        summary=f"Created organization '{organization.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"slug": organization.slug},
    )
    return organization


@router.post("/{org_id}/members", response_model=OrganizationMembershipRead, status_code=status.HTTP_201_CREATED, summary="Add organization member")
def create_organization_member(
    org_id: int,
    payload: OrganizationMembershipCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_org_admin_user),
) -> OrganizationMembershipRead:
    organization = get_organization_or_404(session, organization_id=org_id)
    require_org_role(session, current_user=current_user, organization_id=org_id, allowed_roles={"owner", "admin"})
    membership = add_member(session, organization=organization, payload=payload)
    create_audit_log(
        session,
        action_type="organization_member_added",
        entity_type="organization_membership",
        entity_id=str(membership.id),
        summary=f"Added user {membership.user_id} to organization '{organization.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"organization_id": organization.id, "role": membership.role, "user_id": membership.user_id},
    )
    return membership


@router.patch("/members/{membership_id}", response_model=OrganizationMembershipRead, summary="Update organization membership")
def patch_organization_membership(
    membership_id: int,
    payload: OrganizationMembershipUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_org_admin_user),
) -> OrganizationMembershipRead:
    membership = get_membership_or_404(session, membership_id=membership_id)
    require_org_role(
        session,
        current_user=current_user,
        organization_id=membership.organization_id,
        allowed_roles={"owner", "admin"},
    )
    updated = update_membership(session, membership=membership, payload=payload)
    create_audit_log(
        session,
        action_type="organization_member_updated",
        entity_type="organization_membership",
        entity_id=str(updated.id),
        summary=f"Updated organization membership {updated.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@router.delete("/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove organization member")
def delete_organization_membership(
    membership_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_org_admin_user),
) -> Response:
    membership = get_membership_or_404(session, membership_id=membership_id)
    require_org_role(
        session,
        current_user=current_user,
        organization_id=membership.organization_id,
        allowed_roles={"owner", "admin"},
    )
    create_audit_log(
        session,
        action_type="organization_member_removed",
        entity_type="organization_membership",
        entity_id=str(membership.id),
        summary=f"Removed user {membership.user_id} from organization {membership.organization_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"organization_id": membership.organization_id, "user_id": membership.user_id},
    )
    remove_member(session, membership=membership)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
