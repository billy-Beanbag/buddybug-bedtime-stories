from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import case as sa_case
from sqlmodel import Session, select

from app.models import BillingRecoveryCase, BillingRecoveryEvent, User
from app.schemas.billing_recovery_schema import BillingRecoveryPromptResponse
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.review_service import utc_now

RECOVERY_SOURCE_TYPES = {"stripe_webhook", "billing_sync", "admin", "internal_rule"}
RECOVERY_STATUS_VALUES = {"open", "recovered", "expired", "ignored"}
RECOVERY_EVENT_TYPES = {
    "billing_failed_detected",
    "payment_method_updated",
    "premium_restored",
    "recovery_prompt_shown",
    "recovery_prompt_dismissed",
    "case_resolved",
    "case_expired",
}
HEALTHY_PREMIUM_STATUSES = {"active", "trialing"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_recovery_source_type(value: str) -> str:
    if value not in RECOVERY_SOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid billing recovery source_type")
    return value


def validate_recovery_status(value: str) -> str:
    if value not in RECOVERY_STATUS_VALUES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid billing recovery status")
    return value


def validate_recovery_event_type(value: str) -> str:
    if value not in RECOVERY_EVENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid billing recovery event type")
    return value


def get_billing_recovery_case_or_404(session: Session, *, case_id: int) -> BillingRecoveryCase:
    recovery_case = session.get(BillingRecoveryCase, case_id)
    if recovery_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing recovery case not found")
    return recovery_case


def list_recovery_events(session: Session, *, recovery_case_id: int) -> list[BillingRecoveryEvent]:
    statement = (
        select(BillingRecoveryEvent)
        .where(BillingRecoveryEvent.recovery_case_id == recovery_case_id)
        .order_by(BillingRecoveryEvent.created_at.asc(), BillingRecoveryEvent.id.asc())
    )
    return list(session.exec(statement).all())


def get_open_recovery_case_for_user(session: Session, *, user_id: int) -> BillingRecoveryCase | None:
    statement = (
        select(BillingRecoveryCase)
        .where(
            BillingRecoveryCase.user_id == user_id,
            BillingRecoveryCase.recovery_status == "open",
        )
        .order_by(BillingRecoveryCase.last_detected_at.desc(), BillingRecoveryCase.id.desc())
    )
    return session.exec(statement).first()


def list_recovery_cases(
    session: Session,
    *,
    recovery_status: str | None = None,
    user_id: int | None = None,
    limit: int = 100,
) -> list[BillingRecoveryCase]:
    statement = (
        select(BillingRecoveryCase)
        .order_by(
            sa_case((BillingRecoveryCase.recovery_status == "open", 0), else_=1),
            BillingRecoveryCase.last_detected_at.desc(),
            BillingRecoveryCase.id.desc(),
        )
        .limit(limit)
    )
    if recovery_status is not None:
        statement = statement.where(BillingRecoveryCase.recovery_status == validate_recovery_status(recovery_status))
    if user_id is not None:
        statement = statement.where(BillingRecoveryCase.user_id == user_id)
    return list(session.exec(statement).all())


def list_recovery_cases_for_user(session: Session, *, user_id: int, limit: int = 100) -> list[BillingRecoveryCase]:
    statement = (
        select(BillingRecoveryCase)
        .where(BillingRecoveryCase.user_id == user_id)
        .order_by(BillingRecoveryCase.first_detected_at.desc(), BillingRecoveryCase.id.desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def add_recovery_event(
    session: Session,
    *,
    recovery_case: BillingRecoveryCase,
    event_type: str,
    summary: str,
) -> BillingRecoveryEvent:
    event = BillingRecoveryEvent(
        recovery_case_id=recovery_case.id,
        event_type=validate_recovery_event_type(event_type),
        summary=summary.strip(),
    )
    return _persist(session, event)


def create_or_update_recovery_case(
    session: Session,
    *,
    user: User,
    source_type: str,
    title: str,
    summary: str,
    external_reference: str | None = None,
    billing_status_snapshot: str | None = None,
    subscription_tier_snapshot: str | None = None,
    detected_at: datetime | None = None,
    expires_at: datetime | None = None,
    notes: str | None = None,
    actor_user: User | None = None,
    request_id: str | None = None,
    event_summary: str | None = None,
) -> BillingRecoveryCase:
    detected_at = detected_at or utc_now()
    normalized_source_type = validate_recovery_source_type(source_type)
    normalized_external_reference = external_reference.strip() if external_reference else None

    existing_open_case: BillingRecoveryCase | None = None
    if normalized_external_reference:
        existing_open_case = session.exec(
            select(BillingRecoveryCase).where(
                BillingRecoveryCase.user_id == user.id,
                BillingRecoveryCase.recovery_status == "open",
                BillingRecoveryCase.external_reference == normalized_external_reference,
            )
        ).first()
    if existing_open_case is None:
        existing_open_case = get_open_recovery_case_for_user(session, user_id=user.id)

    created = existing_open_case is None
    recovery_case = existing_open_case or BillingRecoveryCase(
        user_id=user.id,
        source_type=normalized_source_type,
        external_reference=normalized_external_reference,
        recovery_status="open",
        first_detected_at=detected_at,
        last_detected_at=detected_at,
        billing_status_snapshot=billing_status_snapshot,
        subscription_tier_snapshot=subscription_tier_snapshot,
        title=title.strip(),
        summary=summary.strip(),
        expires_at=expires_at,
        notes=notes.strip() if notes is not None and notes.strip() else None,
    )

    recovery_case.source_type = normalized_source_type
    recovery_case.external_reference = normalized_external_reference or recovery_case.external_reference
    recovery_case.recovery_status = "open"
    recovery_case.billing_status_snapshot = billing_status_snapshot
    recovery_case.subscription_tier_snapshot = subscription_tier_snapshot
    recovery_case.title = title.strip()
    recovery_case.summary = summary.strip()
    recovery_case.last_detected_at = detected_at
    recovery_case.expires_at = expires_at
    if notes is not None:
        recovery_case.notes = notes.strip() if notes.strip() else None
    recovery_case.updated_at = utc_now()

    persisted_case = _persist(session, recovery_case)
    add_recovery_event(
        session,
        recovery_case=persisted_case,
        event_type="billing_failed_detected",
        summary=(event_summary or summary).strip(),
    )
    if created:
        create_audit_log(
            session,
            action_type="billing_recovery_case_created",
            entity_type="billing_recovery_case",
            entity_id=str(persisted_case.id),
            summary=f"Opened billing recovery case for user {user.email}",
            actor_user=actor_user,
            request_id=request_id,
            metadata={
                "user_id": user.id,
                "source_type": persisted_case.source_type,
                "external_reference": persisted_case.external_reference,
                "billing_status_snapshot": persisted_case.billing_status_snapshot,
            },
        )
        track_event_safe(
            session,
            event_name="billing_recovery_case_opened",
            user=user,
            metadata={
                "recovery_case_id": persisted_case.id,
                "source_type": persisted_case.source_type,
                "billing_status_snapshot": persisted_case.billing_status_snapshot,
            },
        )
    return persisted_case


def update_recovery_case(
    session: Session,
    *,
    recovery_case: BillingRecoveryCase,
    recovery_status: str | None = None,
    notes: str | None = None,
    resolved_at: datetime | None = None,
    expires_at: datetime | None = None,
    notes_provided: bool = False,
    resolved_at_provided: bool = False,
    expires_at_provided: bool = False,
) -> BillingRecoveryCase:
    if recovery_status is not None:
        recovery_case.recovery_status = validate_recovery_status(recovery_status)
    if notes_provided:
        recovery_case.notes = notes.strip() if notes is not None and notes.strip() else None
    if resolved_at_provided:
        recovery_case.resolved_at = resolved_at
    if expires_at_provided:
        recovery_case.expires_at = expires_at
    recovery_case.updated_at = utc_now()
    return _persist(session, recovery_case)


def resolve_recovery_case(
    session: Session,
    *,
    recovery_case: BillingRecoveryCase,
    actor_user: User | None = None,
    request_id: str | None = None,
    resolution_summary: str = "Premium access was restored.",
    add_premium_restored_event: bool = False,
) -> BillingRecoveryCase:
    if recovery_case.recovery_status != "open":
        return recovery_case

    if add_premium_restored_event:
        add_recovery_event(
            session,
            recovery_case=recovery_case,
            event_type="premium_restored",
            summary="Premium access returned to a healthy state.",
        )

    recovery_case.recovery_status = "recovered"
    recovery_case.resolved_at = utc_now()
    recovery_case.updated_at = utc_now()
    persisted_case = _persist(session, recovery_case)
    add_recovery_event(
        session,
        recovery_case=persisted_case,
        event_type="case_resolved",
        summary=resolution_summary.strip(),
    )
    create_audit_log(
        session,
        action_type="billing_recovery_case_resolved",
        entity_type="billing_recovery_case",
        entity_id=str(persisted_case.id),
        summary=f"Resolved billing recovery case {persisted_case.id}",
        actor_user=actor_user,
        request_id=request_id,
        metadata={"recovery_status": persisted_case.recovery_status, "user_id": persisted_case.user_id},
    )
    user = session.get(User, persisted_case.user_id)
    track_event_safe(
        session,
        event_name="billing_recovery_case_resolved",
        user=user,
        user_id=persisted_case.user_id,
        metadata={"recovery_case_id": persisted_case.id},
    )
    return persisted_case


def expire_recovery_case(
    session: Session,
    *,
    recovery_case: BillingRecoveryCase,
    summary: str = "Billing recovery case expired without account recovery.",
) -> BillingRecoveryCase:
    if recovery_case.recovery_status != "open":
        return recovery_case
    recovery_case.recovery_status = "expired"
    recovery_case.expires_at = recovery_case.expires_at or utc_now()
    recovery_case.updated_at = utc_now()
    persisted_case = _persist(session, recovery_case)
    add_recovery_event(session, recovery_case=persisted_case, event_type="case_expired", summary=summary)
    return persisted_case


def _can_open_recovery_case(*, user: User, source_type: str, external_reference: str | None) -> bool:
    if source_type in {"admin", "internal_rule"}:
        return True
    return bool(external_reference or user.stripe_subscription_id)


def _has_healthy_premium_state(user: User) -> bool:
    if user.subscription_tier != "premium":
        return False
    return user.subscription_status in HEALTHY_PREMIUM_STATUSES


def sync_recovery_from_subscription_state(
    session: Session,
    *,
    user: User,
    source_type: str,
    external_reference: str | None = None,
    actor_user: User | None = None,
    request_id: str | None = None,
) -> BillingRecoveryCase | None:
    normalized_source_type = validate_recovery_source_type(source_type)
    open_case = get_open_recovery_case_for_user(session, user_id=user.id)

    if user.subscription_status == "past_due" and _can_open_recovery_case(
        user=user,
        source_type=normalized_source_type,
        external_reference=external_reference,
    ):
        return create_or_update_recovery_case(
            session,
            user=user,
            source_type=normalized_source_type,
            external_reference=external_reference or user.stripe_subscription_id,
            billing_status_snapshot=user.subscription_status,
            subscription_tier_snapshot=user.subscription_tier,
            title="Billing update needed",
            summary="We could not renew this premium subscription. Update billing details to keep Buddybug premium available.",
            actor_user=actor_user,
            request_id=request_id,
            event_summary="Buddybug detected a failed premium renewal and opened a billing recovery case.",
        )

    if open_case is None:
        return None

    open_case.billing_status_snapshot = user.subscription_status
    open_case.subscription_tier_snapshot = user.subscription_tier
    open_case.last_detected_at = utc_now()
    if user.subscription_status in {"canceled", "expired"}:
        open_case.title = "Restore premium access"
        open_case.summary = (
            "Buddybug premium access is no longer healthy after a billing issue. Review billing details to restore access."
        )
        open_case.updated_at = utc_now()
        return _persist(session, open_case)

    if _has_healthy_premium_state(user):
        return resolve_recovery_case(
            session,
            recovery_case=open_case,
            actor_user=actor_user,
            request_id=request_id,
            resolution_summary="Premium access returned to a healthy state.",
            add_premium_restored_event=True,
        )

    return open_case


def build_recovery_prompt(
    session: Session,
    *,
    user: User,
) -> BillingRecoveryPromptResponse:
    recovery_case = get_open_recovery_case_for_user(session, user_id=user.id)
    if recovery_case is None:
        return BillingRecoveryPromptResponse(has_open_recovery=False)

    if recovery_case.billing_status_snapshot == "past_due" or user.subscription_status == "past_due":
        return BillingRecoveryPromptResponse(
            has_open_recovery=True,
            case=recovery_case,
            action_label="Update Billing",
            action_route="/profile?billing_recovery=1",
            message="We had trouble renewing your premium plan. Update your billing details to keep reading and audio running smoothly.",
        )

    return BillingRecoveryPromptResponse(
        has_open_recovery=True,
        case=recovery_case,
        action_label="Restore Premium",
        action_route="/profile?billing_recovery=1",
        message="Premium access needs attention. Review billing details to restore your family account smoothly.",
    )
