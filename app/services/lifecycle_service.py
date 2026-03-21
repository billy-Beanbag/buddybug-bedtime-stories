from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    AccountHealthSnapshot,
    AnalyticsEvent,
    AuditLog,
    BillingRecoveryCase,
    ChildProfile,
    GiftSubscription,
    LifecycleMilestone,
    OnboardingState,
    PromoAccessCode,
    PromoAccessRedemption,
    ReadingProgress,
    ReferralAttribution,
    SupportTicket,
    User,
    UserEngagementState,
)
from app.schemas.lifecycle_schema import (
    LifecycleRebuildResponse,
    LifecycleSummaryResponse,
    LifecycleTimelineResponse,
)

LIFECYCLE_MILESTONE_TYPES = {
    "account_created",
    "onboarding_started",
    "onboarding_completed",
    "child_profile_created",
    "first_story_opened",
    "first_story_completed",
    "referral_attributed",
    "premium_started",
    "premium_recovered",
    "gift_redeemed",
    "promo_redeemed",
    "support_ticket_created",
    "support_ticket_resolved",
    "billing_recovery_opened",
    "billing_recovery_resolved",
    "churn_risk_detected",
    "dormant_detected",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_metadata(metadata: dict[str, Any] | None) -> str | None:
    if not metadata:
        return None
    return json.dumps(metadata, default=str, sort_keys=True)


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_milestone_type(value: str) -> str:
    if value not in LIFECYCLE_MILESTONE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid lifecycle milestone type")
    return value


def create_lifecycle_milestone(
    session: Session,
    *,
    user_id: int,
    milestone_type: str,
    occurred_at: datetime,
    title: str,
    summary: str | None = None,
    source_table: str | None = None,
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> LifecycleMilestone:
    milestone = LifecycleMilestone(
        user_id=user_id,
        milestone_type=validate_milestone_type(milestone_type),
        occurred_at=_normalize_datetime(occurred_at) or utc_now(),
        title=title.strip(),
        summary=summary.strip() if summary is not None and summary.strip() else None,
        source_table=source_table,
        source_id=source_id,
        metadata_json=_serialize_metadata(metadata),
    )
    return _persist(session, milestone)


def upsert_lifecycle_milestone(
    session: Session,
    *,
    user_id: int,
    milestone_type: str,
    occurred_at: datetime,
    title: str,
    summary: str | None = None,
    source_table: str | None = None,
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[LifecycleMilestone, bool]:
    normalized_type = validate_milestone_type(milestone_type)
    statement = select(LifecycleMilestone).where(
        LifecycleMilestone.user_id == user_id,
        LifecycleMilestone.milestone_type == normalized_type,
        LifecycleMilestone.source_table == source_table,
        LifecycleMilestone.source_id == source_id,
    )
    existing = session.exec(statement).first()
    if existing is None:
        return (
            create_lifecycle_milestone(
                session,
                user_id=user_id,
                milestone_type=normalized_type,
                occurred_at=occurred_at,
                title=title,
                summary=summary,
                source_table=source_table,
                source_id=source_id,
                metadata=metadata,
            ),
            True,
        )

    existing.title = title.strip()
    existing.summary = summary.strip() if summary is not None and summary.strip() else None
    existing.metadata_json = _serialize_metadata(metadata)
    existing.updated_at = utc_now()
    return _persist(session, existing), False


def list_lifecycle_milestones_for_user(session: Session, *, user_id: int) -> list[LifecycleMilestone]:
    statement = (
        select(LifecycleMilestone)
        .where(LifecycleMilestone.user_id == user_id)
        .order_by(LifecycleMilestone.occurred_at.asc(), LifecycleMilestone.id.asc())
    )
    return list(session.exec(statement).all())


def _get_user_or_404(session: Session, *, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _earliest_story_open(session: Session, *, user: User) -> tuple[datetime, str, str, dict[str, Any], str] | None:
    candidates: list[tuple[datetime, str, str, dict[str, Any], str]] = []
    analytics_events = list(
        session.exec(
            select(AnalyticsEvent)
            .where(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.event_name.in_(("book_opened", "onboarding_first_story_opened")),
            )
            .order_by(AnalyticsEvent.occurred_at.asc(), AnalyticsEvent.id.asc())
        ).all()
    )
    if analytics_events:
        event = analytics_events[0]
        candidates.append(
            (
                _normalize_datetime(event.occurred_at) or utc_now(),
                "analytics_event",
                str(event.id),
                {"event_name": event.event_name, "book_id": event.book_id},
                "Opened the first story in Buddybug.",
            )
        )

    reading_progresses = list(
        session.exec(
            select(ReadingProgress)
            .where(ReadingProgress.reader_identifier == f"user:{user.id}")
            .order_by(ReadingProgress.last_opened_at.asc(), ReadingProgress.id.asc())
        ).all()
    )
    if reading_progresses:
        progress = reading_progresses[0]
        candidates.append(
            (
                _normalize_datetime(progress.last_opened_at) or _normalize_datetime(progress.created_at) or utc_now(),
                "reading_progress",
                str(progress.id),
                {"book_id": progress.book_id, "child_profile_id": progress.child_profile_id},
                "Opened the first tracked story session.",
            )
        )

    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1], item[2]))


def _earliest_story_completed(session: Session, *, user: User) -> tuple[datetime, str, str, dict[str, Any], str] | None:
    candidates: list[tuple[datetime, str, str, dict[str, Any], str]] = []
    analytics_events = list(
        session.exec(
            select(AnalyticsEvent)
            .where(AnalyticsEvent.user_id == user.id, AnalyticsEvent.event_name == "book_completed")
            .order_by(AnalyticsEvent.occurred_at.asc(), AnalyticsEvent.id.asc())
        ).all()
    )
    if analytics_events:
        event = analytics_events[0]
        candidates.append(
            (
                _normalize_datetime(event.occurred_at) or utc_now(),
                "analytics_event",
                str(event.id),
                {"event_name": event.event_name, "book_id": event.book_id},
                "Completed the first story in Buddybug.",
            )
        )

    completed_progresses = list(
        session.exec(
            select(ReadingProgress)
            .where(
                ReadingProgress.reader_identifier == f"user:{user.id}",
                ReadingProgress.completed.is_(True),
            )
            .order_by(ReadingProgress.updated_at.asc(), ReadingProgress.id.asc())
        ).all()
    )
    if completed_progresses:
        progress = completed_progresses[0]
        candidates.append(
            (
                _normalize_datetime(progress.updated_at) or _normalize_datetime(progress.last_opened_at) or utc_now(),
                "reading_progress",
                str(progress.id),
                {"book_id": progress.book_id, "child_profile_id": progress.child_profile_id},
                "Completed the first tracked story session.",
            )
        )

    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1], item[2]))


def _current_premium_started_candidate(session: Session, *, user: User) -> tuple[datetime, str, str, dict[str, Any], str] | None:
    if user.subscription_tier != "premium" and user.subscription_status not in {"active", "trialing", "past_due"}:
        return None

    checkout_event = session.exec(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.user_id == user.id, AnalyticsEvent.event_name == "checkout_completed")
        .order_by(AnalyticsEvent.occurred_at.asc(), AnalyticsEvent.id.asc())
    ).first()
    if checkout_event is not None:
        return (
            _normalize_datetime(checkout_event.occurred_at) or utc_now(),
            "analytics_event",
            str(checkout_event.id),
            {"event_name": checkout_event.event_name},
            "Started paid premium access after checkout completed.",
        )

    premium_audit = session.exec(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "user_subscription",
            AuditLog.entity_id == str(user.id),
            AuditLog.action_type.in_(("subscription_trial_granted", "subscription_premium_activated")),
        )
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
    ).first()
    if premium_audit is not None:
        return (
            _normalize_datetime(premium_audit.created_at) or utc_now(),
            "audit_log",
            str(premium_audit.id),
            {"action_type": premium_audit.action_type},
            "Premium access started through an internal subscription action.",
        )

    if user.stripe_subscription_id:
        return (
            _normalize_datetime(user.updated_at) or _normalize_datetime(user.created_at) or utc_now(),
            "user",
            f"{user.id}:current_premium",
            {"subscription_status": user.subscription_status, "stripe_subscription_id": user.stripe_subscription_id},
            "Premium access is currently active and the start was inferred from current subscription state.",
        )
    return None


def rebuild_user_lifecycle_milestones(session: Session, *, user_id: int) -> LifecycleRebuildResponse:
    user = _get_user_or_404(session, user_id=user_id)
    created_count = 0
    seen_premium_source_keys: set[tuple[str | None, str | None]] = set()

    _milestone, created = upsert_lifecycle_milestone(
        session,
        user_id=user.id,
        milestone_type="account_created",
        occurred_at=user.created_at,
        title="Account created",
        summary="Created a Buddybug family account.",
        source_table="user",
        source_id=str(user.id),
        metadata={"email": user.email},
    )
    created_count += int(created)

    onboarding_state = session.exec(select(OnboardingState).where(OnboardingState.user_id == user.id)).first()
    if onboarding_state is not None:
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="onboarding_started",
            occurred_at=onboarding_state.created_at,
            title="Onboarding started",
            summary=f"Started onboarding at step '{onboarding_state.current_step}'.",
            source_table="onboardingstate",
            source_id=str(onboarding_state.id),
            metadata={"current_step": onboarding_state.current_step},
        )
        created_count += int(created)
        if onboarding_state.completed:
            completed_at = onboarding_state.completed_at or onboarding_state.updated_at
            _milestone, created = upsert_lifecycle_milestone(
                session,
                user_id=user.id,
                milestone_type="onboarding_completed",
                occurred_at=completed_at,
                title="Onboarding completed",
                summary="Finished the first-run onboarding flow.",
                source_table="onboardingstate",
                source_id=str(onboarding_state.id),
                metadata={"skipped": onboarding_state.skipped},
            )
            created_count += int(created)

    child_profiles = list(
        session.exec(
            select(ChildProfile)
            .where(ChildProfile.user_id == user.id)
            .order_by(ChildProfile.created_at.asc(), ChildProfile.id.asc())
        ).all()
    )
    for child_profile in child_profiles:
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="child_profile_created",
            occurred_at=child_profile.created_at,
            title="Child profile created",
            summary=f"Added child profile '{child_profile.display_name}'.",
            source_table="childprofile",
            source_id=str(child_profile.id),
            metadata={"age_band": child_profile.age_band, "language": child_profile.language},
        )
        created_count += int(created)

    first_story_opened = _earliest_story_open(session, user=user)
    if first_story_opened is not None:
        occurred_at, source_table, source_id, metadata, summary = first_story_opened
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="first_story_opened",
            occurred_at=occurred_at,
            title="First story opened",
            summary=summary,
            source_table=source_table,
            source_id=source_id,
            metadata=metadata,
        )
        created_count += int(created)

    first_story_completed = _earliest_story_completed(session, user=user)
    if first_story_completed is not None:
        occurred_at, source_table, source_id, metadata, summary = first_story_completed
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="first_story_completed",
            occurred_at=occurred_at,
            title="First story completed",
            summary=summary,
            source_table=source_table,
            source_id=source_id,
            metadata=metadata,
        )
        created_count += int(created)

    referral = session.exec(select(ReferralAttribution).where(ReferralAttribution.referred_user_id == user.id)).first()
    if referral is not None:
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="referral_attributed",
            occurred_at=referral.signup_attributed_at,
            title="Referral attributed",
            summary=f"Signup was attributed to referrer user #{referral.referrer_user_id}.",
            source_table="referralattribution",
            source_id=str(referral.id),
            metadata={"referrer_user_id": referral.referrer_user_id, "referral_code_id": referral.referral_code_id},
        )
        created_count += int(created)
        if referral.premium_converted_at is not None:
            key = ("referralattribution", str(referral.id))
            seen_premium_source_keys.add(key)
            _milestone, created = upsert_lifecycle_milestone(
                session,
                user_id=user.id,
                milestone_type="premium_started",
                occurred_at=referral.premium_converted_at,
                title="Premium started",
                summary="Converted from referral signup into premium access.",
                source_table=key[0],
                source_id=key[1],
                metadata={"referrer_user_id": referral.referrer_user_id},
            )
            created_count += int(created)

    gifts = list(
        session.exec(
            select(GiftSubscription)
            .where(GiftSubscription.recipient_user_id == user.id, GiftSubscription.redeemed_at.is_not(None))
            .order_by(GiftSubscription.redeemed_at.asc(), GiftSubscription.id.asc())
        ).all()
    )
    for gift in gifts:
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="gift_redeemed",
            occurred_at=gift.redeemed_at,
            title="Gift redeemed",
            summary=f"Redeemed a gift subscription for {gift.duration_days} days of premium access.",
            source_table="giftsubscription",
            source_id=str(gift.id),
            metadata={"duration_days": gift.duration_days, "purchaser_user_id": gift.purchaser_user_id},
        )
        created_count += int(created)
        key = ("giftsubscription", str(gift.id))
        seen_premium_source_keys.add(key)
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="premium_started",
            occurred_at=gift.redeemed_at,
            title="Premium started",
            summary="Premium access started from a redeemed gift subscription.",
            source_table=key[0],
            source_id=key[1],
            metadata={"duration_days": gift.duration_days},
        )
        created_count += int(created)

    promo_redemptions = list(
        session.exec(
            select(PromoAccessRedemption)
            .where(PromoAccessRedemption.user_id == user.id)
            .order_by(PromoAccessRedemption.redeemed_at.asc(), PromoAccessRedemption.id.asc())
        ).all()
    )
    for promo_redemption in promo_redemptions:
        promo_code = session.get(PromoAccessCode, promo_redemption.promo_access_code_id)
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="promo_redeemed",
            occurred_at=promo_redemption.redeemed_at,
            title="Promo redeemed",
            summary=f"Redeemed promo access '{promo_code.name}'." if promo_code is not None else "Redeemed promo access.",
            source_table="promoaccessredemption",
            source_id=str(promo_redemption.id),
            metadata={
                "promo_access_code_id": promo_redemption.promo_access_code_id,
                "promo_code_key": promo_code.key if promo_code is not None else None,
            },
        )
        created_count += int(created)
        key = ("promoaccessredemption", str(promo_redemption.id))
        seen_premium_source_keys.add(key)
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="premium_started",
            occurred_at=promo_redemption.redeemed_at,
            title="Premium started",
            summary="Premium access started from redeemed promo access.",
            source_table=key[0],
            source_id=key[1],
            metadata={"promo_access_code_id": promo_redemption.promo_access_code_id},
        )
        created_count += int(created)

    generic_premium_start = _current_premium_started_candidate(session, user=user)
    if generic_premium_start is not None:
        occurred_at, source_table, source_id, metadata, summary = generic_premium_start
        key = (source_table, source_id)
        if key not in seen_premium_source_keys:
            _milestone, created = upsert_lifecycle_milestone(
                session,
                user_id=user.id,
                milestone_type="premium_started",
                occurred_at=occurred_at,
                title="Premium started",
                summary=summary,
                source_table=source_table,
                source_id=source_id,
                metadata=metadata,
            )
            created_count += int(created)

    support_tickets = list(
        session.exec(
            select(SupportTicket)
            .where(SupportTicket.user_id == user.id)
            .order_by(SupportTicket.created_at.asc(), SupportTicket.id.asc())
        ).all()
    )
    for ticket in support_tickets:
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="support_ticket_created",
            occurred_at=ticket.created_at,
            title="Support ticket created",
            summary=f"Opened support ticket '{ticket.subject}'.",
            source_table="supportticket",
            source_id=str(ticket.id),
            metadata={"category": ticket.category, "status": ticket.status, "priority": ticket.priority},
        )
        created_count += int(created)
        if ticket.resolved_at is not None:
            _milestone, created = upsert_lifecycle_milestone(
                session,
                user_id=user.id,
                milestone_type="support_ticket_resolved",
                occurred_at=ticket.resolved_at,
                title="Support ticket resolved",
                summary=f"Resolved support ticket '{ticket.subject}'.",
                source_table="supportticket",
                source_id=str(ticket.id),
                metadata={"category": ticket.category, "status": ticket.status},
            )
            created_count += int(created)

    recovery_cases = list(
        session.exec(
            select(BillingRecoveryCase)
            .where(BillingRecoveryCase.user_id == user.id)
            .order_by(BillingRecoveryCase.first_detected_at.asc(), BillingRecoveryCase.id.asc())
        ).all()
    )
    for recovery_case in recovery_cases:
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="billing_recovery_opened",
            occurred_at=recovery_case.first_detected_at,
            title="Billing recovery opened",
            summary=recovery_case.summary,
            source_table="billingrecoverycase",
            source_id=str(recovery_case.id),
            metadata={"recovery_status": recovery_case.recovery_status, "source_type": recovery_case.source_type},
        )
        created_count += int(created)
        if recovery_case.recovery_status == "recovered" and recovery_case.resolved_at is not None:
            _milestone, created = upsert_lifecycle_milestone(
                session,
                user_id=user.id,
                milestone_type="billing_recovery_resolved",
                occurred_at=recovery_case.resolved_at,
                title="Billing recovery resolved",
                summary="Recovered premium billing health after follow-up.",
                source_table="billingrecoverycase",
                source_id=str(recovery_case.id),
                metadata={"source_type": recovery_case.source_type},
            )
            created_count += int(created)
            _milestone, created = upsert_lifecycle_milestone(
                session,
                user_id=user.id,
                milestone_type="premium_recovered",
                occurred_at=recovery_case.resolved_at,
                title="Premium recovered",
                summary="Premium access returned after a billing recovery flow.",
                source_table="billingrecoverycase",
                source_id=str(recovery_case.id),
                metadata={"source_type": recovery_case.source_type},
            )
            created_count += int(created)

    engagement_state = session.exec(select(UserEngagementState).where(UserEngagementState.user_id == user.id)).first()
    if engagement_state is not None:
        if engagement_state.state_key in {"dormant_7d", "dormant_30d"}:
            _milestone, created = upsert_lifecycle_milestone(
                session,
                user_id=user.id,
                milestone_type="dormant_detected",
                occurred_at=engagement_state.generated_at,
                title="Dormancy detected",
                summary=f"Engagement state shifted to '{engagement_state.state_key}'.",
                source_table="userengagementstate",
                source_id=str(engagement_state.id),
                metadata={"state_key": engagement_state.state_key},
            )
            created_count += int(created)
        if engagement_state.state_key == "lapsed_premium":
            _milestone, created = upsert_lifecycle_milestone(
                session,
                user_id=user.id,
                milestone_type="churn_risk_detected",
                occurred_at=engagement_state.generated_at,
                title="Churn risk detected",
                summary="User engagement signals indicate lapsed premium risk.",
                source_table="userengagementstate",
                source_id=str(engagement_state.id),
                metadata={"state_key": engagement_state.state_key},
            )
            created_count += int(created)

    account_health = session.exec(select(AccountHealthSnapshot).where(AccountHealthSnapshot.user_id == user.id)).first()
    if account_health is not None and account_health.health_band in {"at_risk", "churned"}:
        _milestone, created = upsert_lifecycle_milestone(
            session,
            user_id=user.id,
            milestone_type="churn_risk_detected",
            occurred_at=account_health.generated_at,
            title="Churn risk detected",
            summary=f"Account health snapshot flagged this user as {account_health.health_band}.",
            source_table="accounthealthsnapshot",
            source_id=str(account_health.id),
            metadata={"health_band": account_health.health_band, "health_score": account_health.health_score},
        )
        created_count += int(created)

    milestones = list_lifecycle_milestones_for_user(session, user_id=user.id)
    return LifecycleRebuildResponse(user_id=user.id, created_count=created_count, milestones=milestones)


def get_user_lifecycle_timeline(session: Session, *, user_id: int) -> LifecycleTimelineResponse:
    _get_user_or_404(session, user_id=user_id)
    return LifecycleTimelineResponse(
        user_id=user_id,
        milestones=list_lifecycle_milestones_for_user(session, user_id=user_id),
    )


def infer_lifecycle_stage(
    *,
    user: User,
    has_completed_onboarding: bool,
    has_child_profiles: bool,
    has_premium_history: bool,
    open_billing_recovery: bool,
    engagement_state: UserEngagementState | None,
    milestone_types: set[str],
) -> str | None:
    if open_billing_recovery:
        return "recovering"
    if engagement_state is not None and engagement_state.state_key in {"dormant_7d", "dormant_30d"}:
        return "dormant"
    if "churn_risk_detected" in milestone_types or (
        engagement_state is not None and engagement_state.state_key == "lapsed_premium"
    ):
        return "at_risk"
    if user.subscription_tier == "premium" and user.subscription_status in {"active", "trialing"}:
        return "premium"
    if has_completed_onboarding and (
        "first_story_opened" in milestone_types or "first_story_completed" in milestone_types or has_child_profiles
    ):
        if "first_story_completed" in milestone_types or (
            engagement_state is not None and engagement_state.state_key == "active"
        ):
            return "engaged"
        return "activated"
    if not has_completed_onboarding and "onboarding_started" in milestone_types:
        return "onboarding"
    if has_premium_history:
        return "activated"
    return "new"


def get_user_lifecycle_summary(session: Session, *, user_id: int) -> LifecycleSummaryResponse:
    user = _get_user_or_404(session, user_id=user_id)
    milestones = list_lifecycle_milestones_for_user(session, user_id=user_id)
    milestone_types = {milestone.milestone_type for milestone in milestones}
    first_seen_at = _normalize_datetime(user.created_at)

    engagement_state = session.exec(select(UserEngagementState).where(UserEngagementState.user_id == user.id)).first()
    support_ticket_count = session.exec(
        select(SupportTicket).where(SupportTicket.user_id == user.id)
    ).all()
    open_billing_recovery = get_open_billing_recovery_for_user(session, user_id=user.id)
    latest_candidates = [milestone.occurred_at for milestone in milestones]
    if engagement_state is not None and engagement_state.last_active_at is not None:
        latest_candidates.append(engagement_state.last_active_at)
    latest_candidates.append(user.updated_at)
    latest_activity_at = max((_normalize_datetime(value) for value in latest_candidates if value is not None), default=None)

    has_completed_onboarding = "onboarding_completed" in milestone_types
    has_child_profiles = "child_profile_created" in milestone_types
    has_premium_history = (
        "premium_started" in milestone_types
        or "premium_recovered" in milestone_types
        or user.subscription_tier == "premium"
        or user.subscription_status in {"active", "trialing", "past_due", "canceled", "expired"}
    )

    return LifecycleSummaryResponse(
        user_id=user.id,
        first_seen_at=first_seen_at,
        latest_activity_at=latest_activity_at,
        has_completed_onboarding=has_completed_onboarding,
        has_child_profiles=has_child_profiles,
        has_premium_history=has_premium_history,
        current_subscription_status=user.subscription_status,
        support_ticket_count=len(support_ticket_count),
        open_billing_recovery=open_billing_recovery,
        lifecycle_stage=infer_lifecycle_stage(
            user=user,
            has_completed_onboarding=has_completed_onboarding,
            has_child_profiles=has_child_profiles,
            has_premium_history=has_premium_history,
            open_billing_recovery=open_billing_recovery,
            engagement_state=engagement_state,
            milestone_types=milestone_types,
        ),
    )


def get_open_billing_recovery_for_user(session: Session, *, user_id: int) -> bool:
    return (
        session.exec(
            select(BillingRecoveryCase).where(
                BillingRecoveryCase.user_id == user_id,
                BillingRecoveryCase.recovery_status == "open",
            )
        ).first()
        is not None
    )
