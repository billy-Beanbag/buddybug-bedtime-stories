from __future__ import annotations

import re
import secrets
from datetime import timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import GiftSubscription, ReferralAttribution, ReferralCode, User
from app.services.analytics_service import track_event_safe
from app.services.billing_recovery_service import sync_recovery_from_subscription_state
from app.services.review_service import utc_now

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ALLOWED_GIFT_DURATIONS = {30, 90, 365}
REFERRAL_CODE_PATTERN = re.compile(r"^[A-Z0-9]{4,16}$")


def normalize_referral_code(code: str) -> str:
    normalized = code.strip().upper()
    if not REFERRAL_CODE_PATTERN.match(normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid referral code format")
    return normalized


def get_or_create_referral_code(session: Session, *, user: User) -> tuple[ReferralCode, bool]:
    statement = select(ReferralCode).where(ReferralCode.user_id == user.id)
    existing = session.exec(statement).first()
    if existing is not None:
        return existing, False

    referral_code = ReferralCode(user_id=user.id, code=generate_referral_code(session, user=user))
    session.add(referral_code)
    session.commit()
    session.refresh(referral_code)
    return referral_code, True


def generate_referral_code(session: Session, *, user: User) -> str:
    base = _code_prefix_from_user(user)
    for _attempt in range(25):
        suffix = "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
        candidate = f"{base}{suffix}"[:12]
        if session.exec(select(ReferralCode).where(ReferralCode.code == candidate)).first() is None:
            return candidate
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate referral code")


def get_referral_code_by_value(session: Session, *, code: str) -> ReferralCode:
    normalized = normalize_referral_code(code)
    statement = select(ReferralCode).where(ReferralCode.code == normalized, ReferralCode.is_active.is_(True))
    referral_code = session.exec(statement).first()
    if referral_code is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referral code not found")
    return referral_code


def attribute_user_to_referral(
    session: Session,
    *,
    referred_user: User,
    referral_code_value: str,
) -> ReferralAttribution:
    existing = session.exec(
        select(ReferralAttribution).where(ReferralAttribution.referred_user_id == referred_user.id)
    ).first()
    if existing is not None:
        return existing

    referral_code = get_referral_code_by_value(session, code=referral_code_value)
    if referral_code.user_id == referred_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Self-referral is not allowed")

    attribution = ReferralAttribution(
        referrer_user_id=referral_code.user_id,
        referred_user_id=referred_user.id,
        referral_code_id=referral_code.id,
    )
    referral_code.total_uses += 1
    referral_code.updated_at = utc_now()
    session.add(referral_code)
    session.add(attribution)
    session.commit()
    session.refresh(referral_code)
    session.refresh(attribution)
    return attribution


def get_referral_summary(session: Session, *, user: User) -> tuple[ReferralCode | None, int, int]:
    referral_code, _created = get_or_create_referral_code(session, user=user)
    attributions = list(
        session.exec(select(ReferralAttribution).where(ReferralAttribution.referrer_user_id == user.id)).all()
    )
    premium_conversions = sum(1 for attribution in attributions if attribution.premium_converted_at is not None)
    return referral_code, len(attributions), premium_conversions


def mark_referral_premium_conversion(session: Session, *, user: User) -> ReferralAttribution | None:
    if not _user_has_premium_access(user):
        return None
    attribution = session.exec(
        select(ReferralAttribution).where(ReferralAttribution.referred_user_id == user.id)
    ).first()
    if attribution is None or attribution.premium_converted_at is not None:
        return None
    attribution.premium_converted_at = utc_now()
    attribution.updated_at = utc_now()
    session.add(attribution)
    session.commit()
    session.refresh(attribution)
    return attribution


def list_referral_attributions(
    session: Session,
    *,
    referrer_user_id: int | None = None,
    referred_user_id: int | None = None,
    limit: int = 100,
) -> list[ReferralAttribution]:
    statement = select(ReferralAttribution).order_by(ReferralAttribution.signup_attributed_at.desc()).limit(limit)
    if referrer_user_id is not None:
        statement = statement.where(ReferralAttribution.referrer_user_id == referrer_user_id)
    if referred_user_id is not None:
        statement = statement.where(ReferralAttribution.referred_user_id == referred_user_id)
    return list(session.exec(statement).all())


def create_gift_subscription(
    session: Session,
    *,
    purchaser_user: User,
    duration_days: int,
    notes: str | None = None,
) -> GiftSubscription:
    if duration_days not in ALLOWED_GIFT_DURATIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported gift duration")
    gift = GiftSubscription(
        purchaser_user_id=purchaser_user.id,
        code=_generate_gift_code(session),
        duration_days=duration_days,
        status="active",
        notes=notes,
    )
    session.add(gift)
    session.commit()
    session.refresh(gift)
    return gift


def list_gifts_for_purchaser(session: Session, *, purchaser_user_id: int) -> list[GiftSubscription]:
    gifts = list(
        session.exec(
            select(GiftSubscription)
            .where(GiftSubscription.purchaser_user_id == purchaser_user_id)
            .order_by(GiftSubscription.purchased_at.desc())
        ).all()
    )
    return [expire_gift_if_needed(session, gift=gift) for gift in gifts]


def list_gifts_for_admin(
    session: Session,
    *,
    status_value: str | None = None,
    purchaser_user_id: int | None = None,
    recipient_user_id: int | None = None,
    limit: int = 100,
) -> list[GiftSubscription]:
    statement = select(GiftSubscription).order_by(GiftSubscription.purchased_at.desc()).limit(limit)
    if status_value is not None:
        statement = statement.where(GiftSubscription.status == status_value)
    if purchaser_user_id is not None:
        statement = statement.where(GiftSubscription.purchaser_user_id == purchaser_user_id)
    if recipient_user_id is not None:
        statement = statement.where(GiftSubscription.recipient_user_id == recipient_user_id)
    gifts = list(session.exec(statement).all())
    return [expire_gift_if_needed(session, gift=gift) for gift in gifts]


def redeem_gift_subscription(
    session: Session,
    *,
    current_user: User,
    code: str,
) -> GiftSubscription:
    normalized = normalize_referral_code(code)
    gift = session.exec(select(GiftSubscription).where(GiftSubscription.code == normalized)).first()
    if gift is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift code not found")

    gift = expire_gift_if_needed(session, gift=gift)
    if gift.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift code is not redeemable")
    if gift.recipient_user_id is not None or gift.redeemed_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift code has already been redeemed")
    if gift.purchaser_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot redeem your own gift")

    apply_gift_subscription_to_user(session, user=current_user, duration_days=gift.duration_days)
    gift.recipient_user_id = current_user.id
    gift.redeemed_at = utc_now()
    gift.status = "redeemed"
    gift.expires_at = current_user.subscription_expires_at
    gift.updated_at = utc_now()
    session.add(gift)
    session.commit()
    session.refresh(gift)
    attribution = mark_referral_premium_conversion(session, user=current_user)
    if attribution is not None:
        track_event_safe(
            session,
            event_name="referral_premium_converted",
            user=current_user,
            metadata={"referrer_user_id": attribution.referrer_user_id, "source": "gift_redemption"},
        )
    return gift


def apply_gift_subscription_to_user(session: Session, *, user: User, duration_days: int) -> User:
    if duration_days not in ALLOWED_GIFT_DURATIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported gift duration")
    now = utc_now()
    base_expiry = user.subscription_expires_at if user.subscription_expires_at and user.subscription_expires_at > now else now
    user.subscription_tier = "premium"
    user.subscription_status = "active"
    user.subscription_expires_at = base_expiry + timedelta(days=duration_days)
    user.trial_ends_at = None
    user.updated_at = now
    session.add(user)
    session.commit()
    session.refresh(user)
    sync_recovery_from_subscription_state(session, user=user, source_type="internal_rule")
    return user


def expire_gift_if_needed(session: Session, *, gift: GiftSubscription) -> GiftSubscription:
    if gift.status == "redeemed" and gift.expires_at is not None and gift.expires_at <= utc_now():
        gift.status = "expired"
        gift.updated_at = utc_now()
        session.add(gift)
        session.commit()
        session.refresh(gift)
    return gift


def _generate_gift_code(session: Session) -> str:
    for _attempt in range(25):
        candidate = "".join(secrets.choice(CODE_ALPHABET) for _ in range(10))
        if session.exec(select(GiftSubscription).where(GiftSubscription.code == candidate)).first() is None:
            return candidate
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate gift code")


def _code_prefix_from_user(user: User) -> str:
    source = (user.display_name or user.email.split("@", 1)[0] or "BUDDY").upper()
    letters = "".join(char for char in source if char.isalnum())
    prefix = (letters[:6] or "BUDDY").ljust(6, "B")
    return prefix


def _user_has_premium_access(user: User) -> bool:
    if user.is_admin:
        return True
    now = utc_now()
    if user.subscription_tier == "premium" and user.subscription_status == "trialing":
        return user.trial_ends_at is None or user.trial_ends_at > now
    if user.subscription_tier == "premium" and user.subscription_status == "active":
        return user.subscription_expires_at is None or user.subscription_expires_at > now
    return False
