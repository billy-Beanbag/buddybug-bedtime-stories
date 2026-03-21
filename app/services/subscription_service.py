from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import User
from app.schemas.subscription_schema import ReaderAccessResponse, SubscriptionAdminUpdate, SubscriptionStatusRead
from app.services.analytics_service import track_event_safe
from app.services.billing_recovery_service import sync_recovery_from_subscription_state
from app.services.growth_service import mark_referral_premium_conversion
from app.services.review_service import utc_now

PREVIEW_PAGE_LIMIT = 2
ALLOWED_SUBSCRIPTION_TIERS = {"free", "premium"}
ALLOWED_SUBSCRIPTION_STATUSES = {"none", "trialing", "active", "past_due", "canceled", "expired"}


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_user_or_404(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def validate_subscription_tier(subscription_tier: str) -> str:
    if subscription_tier not in ALLOWED_SUBSCRIPTION_TIERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subscription tier")
    return subscription_tier


def validate_subscription_status(subscription_status: str) -> str:
    if subscription_status not in ALLOWED_SUBSCRIPTION_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subscription status")
    return subscription_status


def is_trial_active(user: User) -> bool:
    if user.subscription_tier != "premium" or user.subscription_status != "trialing":
        return False
    trial_ends_at = _normalize_datetime(user.trial_ends_at)
    if trial_ends_at is not None and trial_ends_at <= utc_now():
        return False
    return True


def is_subscription_active(user: User) -> bool:
    if user.subscription_tier != "premium" or user.subscription_status != "active":
        return False
    subscription_expires_at = _normalize_datetime(user.subscription_expires_at)
    if subscription_expires_at is not None and subscription_expires_at <= utc_now():
        return False
    return True


def has_premium_access(user: User | None) -> bool:
    if user is None:
        return False
    if user.is_admin:
        return True
    return is_trial_active(user) or is_subscription_active(user)


def get_preview_page_limit(_: User | None) -> int:
    return PREVIEW_PAGE_LIMIT


def build_subscription_status_read(user: User) -> SubscriptionStatusRead:
    return SubscriptionStatusRead(
        user_id=user.id,
        subscription_tier=user.subscription_tier,
        subscription_status=user.subscription_status,
        subscription_expires_at=user.subscription_expires_at,
        trial_ends_at=user.trial_ends_at,
        has_premium_access=has_premium_access(user),
        is_trial_active=is_trial_active(user),
        is_subscription_active=is_subscription_active(user),
    )


def get_reader_access_for_user(user: User | None, book_id: int) -> ReaderAccessResponse:
    if user is not None and has_premium_access(user):
        return ReaderAccessResponse(
            book_id=book_id,
            can_read_full_book=True,
            can_use_audio=True,
            preview_page_limit=PREVIEW_PAGE_LIMIT,
            reason="Premium access active",
        )

    if user is not None:
        return ReaderAccessResponse(
            book_id=book_id,
            can_read_full_book=False,
            can_use_audio=False,
            preview_page_limit=PREVIEW_PAGE_LIMIT,
            reason="Premium subscription required for full books and audio",
        )

    return ReaderAccessResponse(
        book_id=book_id,
        can_read_full_book=False,
        can_use_audio=False,
        preview_page_limit=PREVIEW_PAGE_LIMIT,
        reason="Guest preview only",
    )


def apply_subscription_admin_update(
    session: Session,
    *,
    user: User,
    payload: SubscriptionAdminUpdate,
) -> User:
    update_data = payload.model_dump(exclude_unset=True)
    if "subscription_tier" in update_data and update_data["subscription_tier"] is not None:
        user.subscription_tier = validate_subscription_tier(update_data["subscription_tier"])
    if "subscription_status" in update_data and update_data["subscription_status"] is not None:
        user.subscription_status = validate_subscription_status(update_data["subscription_status"])
    if "subscription_expires_at" in update_data:
        user.subscription_expires_at = update_data["subscription_expires_at"]
    if "trial_ends_at" in update_data:
        user.trial_ends_at = update_data["trial_ends_at"]
    user.updated_at = utc_now()
    session.add(user)
    session.commit()
    session.refresh(user)
    attribution = mark_referral_premium_conversion(session, user=user)
    if attribution is not None:
        track_event_safe(
            session,
            event_name="referral_premium_converted",
            user=user,
            metadata={"referrer_user_id": attribution.referrer_user_id},
        )
    sync_recovery_from_subscription_state(session, user=user, source_type="admin")
    return user


def grant_trial(
    session: Session,
    *,
    user: User,
    days: int,
) -> User:
    if days < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="days must be at least 1")
    user.subscription_tier = "premium"
    user.subscription_status = "trialing"
    user.trial_ends_at = utc_now() + timedelta(days=days)
    user.subscription_expires_at = None
    user.updated_at = utc_now()
    session.add(user)
    session.commit()
    session.refresh(user)
    attribution = mark_referral_premium_conversion(session, user=user)
    if attribution is not None:
        track_event_safe(
            session,
            event_name="referral_premium_converted",
            user=user,
            metadata={"referrer_user_id": attribution.referrer_user_id},
        )
    sync_recovery_from_subscription_state(session, user=user, source_type="admin")
    return user


def activate_premium(session: Session, *, user: User) -> User:
    user.subscription_tier = "premium"
    user.subscription_status = "active"
    user.trial_ends_at = None
    user.updated_at = utc_now()
    session.add(user)
    session.commit()
    session.refresh(user)
    attribution = mark_referral_premium_conversion(session, user=user)
    if attribution is not None:
        track_event_safe(
            session,
            event_name="referral_premium_converted",
            user=user,
            metadata={"referrer_user_id": attribution.referrer_user_id},
        )
    sync_recovery_from_subscription_state(session, user=user, source_type="admin")
    return user


def revoke_premium(session: Session, *, user: User) -> User:
    user.subscription_tier = "free"
    user.subscription_status = "expired"
    user.subscription_expires_at = None
    user.trial_ends_at = None
    user.updated_at = utc_now()
    session.add(user)
    session.commit()
    session.refresh(user)
    sync_recovery_from_subscription_state(session, user=user, source_type="admin")
    return user
