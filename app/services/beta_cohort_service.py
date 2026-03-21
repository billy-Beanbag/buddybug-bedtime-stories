from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import BetaCohort, BetaCohortMembership, User
from app.services.user_service import get_user_by_id

BETA_MEMBERSHIP_SOURCES = {"admin", "invite_code", "migration", "internal"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _normalize_csv(value: str | None) -> str | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return ",".join(items) if items else None


def validate_membership_source(source: str) -> str:
    if source not in BETA_MEMBERSHIP_SOURCES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid beta cohort membership source")
    return source


def get_beta_cohort_or_404(session: Session, *, cohort_id: int) -> BetaCohort:
    cohort = session.get(BetaCohort, cohort_id)
    if cohort is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beta cohort not found")
    return cohort


def get_beta_membership_or_404(session: Session, *, membership_id: int) -> BetaCohortMembership:
    membership = session.get(BetaCohortMembership, membership_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beta cohort membership not found")
    return membership


def list_cohorts(session: Session) -> list[BetaCohort]:
    return list(session.exec(select(BetaCohort).order_by(BetaCohort.name.asc())).all())


def list_cohort_memberships(session: Session, *, cohort_id: int) -> list[BetaCohortMembership]:
    return list(
        session.exec(
            select(BetaCohortMembership)
            .where(BetaCohortMembership.beta_cohort_id == cohort_id)
            .order_by(BetaCohortMembership.joined_at.desc(), BetaCohortMembership.id.desc())
        ).all()
    )


def create_beta_cohort(
    session: Session,
    *,
    key: str,
    name: str,
    description: str | None,
    is_active: bool,
    feature_flag_keys: str | None,
    notes: str | None,
    created_by_user_id: int | None,
) -> BetaCohort:
    normalized_key = key.strip().lower()
    existing = session.exec(select(BetaCohort).where(BetaCohort.key == normalized_key)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Beta cohort key already exists")
    cohort = BetaCohort(
        key=normalized_key,
        name=name.strip(),
        description=description.strip() if description is not None and description.strip() else None,
        is_active=is_active,
        feature_flag_keys=_normalize_csv(feature_flag_keys),
        notes=notes.strip() if notes is not None and notes.strip() else None,
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, cohort)


def update_beta_cohort(
    session: Session,
    *,
    cohort: BetaCohort,
    key: str | None = None,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
    feature_flag_keys: str | None = None,
    notes: str | None = None,
    description_provided: bool = False,
    feature_flag_keys_provided: bool = False,
    notes_provided: bool = False,
) -> BetaCohort:
    if key is not None:
        normalized_key = key.strip().lower()
        if normalized_key != cohort.key:
            existing = session.exec(select(BetaCohort).where(BetaCohort.key == normalized_key)).first()
            if existing is not None and existing.id != cohort.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Beta cohort key already exists")
            cohort.key = normalized_key
    if name is not None:
        cohort.name = name.strip()
    if description_provided:
        cohort.description = description.strip() if description is not None and description.strip() else None
    if is_active is not None:
        cohort.is_active = is_active
    if feature_flag_keys_provided:
        cohort.feature_flag_keys = _normalize_csv(feature_flag_keys)
    if notes_provided:
        cohort.notes = notes.strip() if notes is not None and notes.strip() else None
    return _persist(session, cohort)


def add_user_to_cohort(
    session: Session,
    *,
    cohort: BetaCohort,
    user_id: int,
    source: str,
    invited_by_user_id: int | None,
    is_active: bool,
) -> BetaCohortMembership:
    user = get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    validate_membership_source(source)
    membership = session.exec(
        select(BetaCohortMembership).where(
            BetaCohortMembership.beta_cohort_id == cohort.id,
            BetaCohortMembership.user_id == user_id,
        )
    ).first()
    if membership is None:
        membership = BetaCohortMembership(
            beta_cohort_id=cohort.id,
            user_id=user_id,
            source=source,
            invited_by_user_id=invited_by_user_id,
            is_active=is_active,
        )
    else:
        membership.source = source
        membership.invited_by_user_id = invited_by_user_id
        membership.is_active = is_active
        if is_active and membership.joined_at is None:
            from app.models.user import utc_now

            membership.joined_at = utc_now()
    return _persist(session, membership)


def update_membership(
    session: Session,
    *,
    membership: BetaCohortMembership,
    is_active: bool | None = None,
) -> BetaCohortMembership:
    if is_active is not None:
        membership.is_active = is_active
    return _persist(session, membership)


def deactivate_membership(session: Session, *, membership: BetaCohortMembership) -> BetaCohortMembership:
    membership.is_active = False
    return _persist(session, membership)


def get_cohort_detail(session: Session, *, cohort_id: int) -> tuple[BetaCohort, list[BetaCohortMembership]]:
    cohort = get_beta_cohort_or_404(session, cohort_id=cohort_id)
    memberships = list_cohort_memberships(session, cohort_id=cohort_id)
    return cohort, memberships


def get_user_beta_cohorts(session: Session, *, user_id: int) -> list[BetaCohort]:
    memberships = list(
        session.exec(
            select(BetaCohortMembership).where(
                BetaCohortMembership.user_id == user_id,
                BetaCohortMembership.is_active.is_(True),
            )
        ).all()
    )
    if not memberships:
        return []
    cohort_ids = [item.beta_cohort_id for item in memberships]
    cohorts = list(
        session.exec(
            select(BetaCohort)
            .where(BetaCohort.id.in_(cohort_ids), BetaCohort.is_active.is_(True))
            .order_by(BetaCohort.name.asc())
        ).all()
    )
    return cohorts


def get_user_beta_cohort_keys(session: Session, *, user_id: int) -> set[str]:
    return {cohort.key.lower() for cohort in get_user_beta_cohorts(session, user_id=user_id)}


def user_in_cohort(session: Session, *, user_id: int, cohort_key: str) -> bool:
    return cohort_key.lower() in get_user_beta_cohort_keys(session, user_id=user_id)
