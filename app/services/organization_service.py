from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Organization, OrganizationMembership, User
from app.schemas.organization_schema import (
    OrganizationCreate,
    OrganizationMembershipCreate,
    OrganizationMembershipRead,
    OrganizationMembershipUpdate,
    OrganizationRead,
    OrganizationUpdate,
)
from app.services.review_service import utc_now

ALLOWED_ORG_ROLES = {"owner", "admin", "editor", "analyst", "support"}
ORG_ADMIN_ROLES = {"owner", "admin"}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _validate_slug(slug: str) -> str:
    normalized = slug.strip().lower()
    if not SLUG_PATTERN.match(normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization slug must be lowercase kebab-case")
    return normalized


def _validate_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized not in ALLOWED_ORG_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported organization role")
    return normalized


def get_organization_or_404(session: Session, *, organization_id: int) -> Organization:
    organization = session.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


def get_membership_or_404(session: Session, *, membership_id: int) -> OrganizationMembership:
    membership = session.get(OrganizationMembership, membership_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization membership not found")
    return membership


def get_active_membership_for_user(session: Session, *, user_id: int) -> OrganizationMembership | None:
    statement = select(OrganizationMembership).where(
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.is_active.is_(True),
    )
    return session.exec(statement).first()


def get_organization_for_user(session: Session, *, user: User) -> Organization | None:
    membership = get_active_membership_for_user(session, user_id=user.id)
    if membership is None:
        return None
    return get_organization_or_404(session, organization_id=membership.organization_id)


def get_active_membership_for_org_user(session: Session, *, user: User, organization_id: int) -> OrganizationMembership | None:
    statement = select(OrganizationMembership).where(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.organization_id == organization_id,
        OrganizationMembership.is_active.is_(True),
    )
    return session.exec(statement).first()


def require_org_role(
    session: Session,
    *,
    current_user: User,
    organization_id: int,
    allowed_roles: set[str],
) -> OrganizationMembership | None:
    if current_user.is_admin:
        return None
    membership = get_active_membership_for_org_user(session, user=current_user, organization_id=organization_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization access required")
    if membership.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization role does not allow this action")
    return membership


def create_organization(session: Session, *, current_user: User, payload: OrganizationCreate) -> Organization:
    if get_active_membership_for_user(session, user_id=current_user.id) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already belongs to an organization")
    normalized_slug = _validate_slug(payload.slug)
    if session.exec(select(Organization).where(Organization.slug == normalized_slug)).first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization slug already exists")
    organization = Organization(name=payload.name, slug=normalized_slug, is_active=payload.is_active)
    session.add(organization)
    session.commit()
    session.refresh(organization)
    owner_membership = OrganizationMembership(
        organization_id=organization.id,
        user_id=current_user.id,
        role="owner",
        is_active=True,
    )
    current_user.organization_id = organization.id
    current_user.updated_at = utc_now()
    session.add(owner_membership)
    session.add(current_user)
    session.commit()
    session.refresh(organization)
    return organization


def update_organization(session: Session, *, organization: Organization, payload: OrganizationUpdate) -> Organization:
    update_data = payload.model_dump(exclude_unset=True)
    if "slug" in update_data and update_data["slug"] is not None:
        update_data["slug"] = _validate_slug(update_data["slug"])
        existing = session.exec(select(Organization).where(Organization.slug == update_data["slug"])).first()
        if existing is not None and existing.id != organization.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization slug already exists")
    for field_name, value in update_data.items():
        setattr(organization, field_name, value)
    organization.updated_at = utc_now()
    return _persist(session, organization)


def add_member(
    session: Session,
    *,
    organization: Organization,
    payload: OrganizationMembershipCreate,
) -> OrganizationMembership:
    user = session.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    role = _validate_role(payload.role)
    active_membership = get_active_membership_for_user(session, user_id=user.id)
    if active_membership is not None and active_membership.organization_id != organization.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already belongs to another organization")
    existing = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization.id,
            OrganizationMembership.user_id == user.id,
        )
    ).first()
    if existing is not None and existing.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this organization")
    if existing is not None:
        existing.role = role
        existing.is_active = payload.is_active
        existing.updated_at = utc_now()
        user.organization_id = organization.id if existing.is_active else None
        user.updated_at = utc_now()
        session.add(existing)
        session.add(user)
        session.commit()
        session.refresh(existing)
        return existing
    membership = OrganizationMembership(
        organization_id=organization.id,
        user_id=user.id,
        role=role,
        is_active=payload.is_active,
    )
    if membership.is_active:
        user.organization_id = organization.id
        user.updated_at = utc_now()
        session.add(user)
    return _persist(session, membership)


def update_membership(
    session: Session,
    *,
    membership: OrganizationMembership,
    payload: OrganizationMembershipUpdate,
) -> OrganizationMembership:
    update_data = payload.model_dump(exclude_unset=True)
    if "role" in update_data and update_data["role"] is not None:
        update_data["role"] = _validate_role(update_data["role"])
    target_user = session.get(User, membership.user_id)
    for field_name, value in update_data.items():
        setattr(membership, field_name, value)
    membership.updated_at = utc_now()
    if target_user is not None:
        if membership.is_active:
            other_active = get_active_membership_for_user(session, user_id=target_user.id)
            if other_active is not None and other_active.id != membership.id and other_active.organization_id != membership.organization_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already belongs to another organization")
            target_user.organization_id = membership.organization_id
        elif target_user.organization_id == membership.organization_id:
            target_user.organization_id = None
        target_user.updated_at = utc_now()
        session.add(target_user)
    return _persist(session, membership)


def remove_member(session: Session, *, membership: OrganizationMembership) -> None:
    target_user = session.get(User, membership.user_id)
    session.delete(membership)
    if target_user is not None and target_user.organization_id == membership.organization_id:
        target_user.organization_id = None
        target_user.updated_at = utc_now()
        session.add(target_user)
    session.commit()


def list_members(session: Session, *, organization_id: int) -> list[OrganizationMembership]:
    statement = (
        select(OrganizationMembership)
        .where(OrganizationMembership.organization_id == organization_id)
        .order_by(OrganizationMembership.created_at.asc())
    )
    return list(session.exec(statement).all())


def get_organization_detail_for_user(session: Session, *, user: User) -> tuple[Organization, list[OrganizationMembership]]:
    organization = get_organization_for_user(session, user=user)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not belong to an organization")
    memberships = list_members(session, organization_id=organization.id)
    return organization, memberships


def build_organization_detail_response(
    *,
    organization: Organization,
    memberships: list[OrganizationMembership],
) -> dict[str, OrganizationRead | list[OrganizationMembershipRead]]:
    return {
        "organization": OrganizationRead.model_validate(organization),
        "memberships": [OrganizationMembershipRead.model_validate(item) for item in memberships],
    }
