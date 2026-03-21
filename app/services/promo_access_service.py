from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import PromoAccessCode, PromoAccessRedemption, User
from app.schemas.promo_access_schema import PromoAccessCodeCreate, PromoAccessCodeUpdate
from app.services.billing_recovery_service import sync_recovery_from_subscription_state
from app.services.review_service import utc_now

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
PROMO_CODE_PATTERN = re.compile(r"^[A-Z0-9]{4,24}$")
ALLOWED_ACCESS_TYPES = {"temporary_premium", "gift_like_access", "feature_unlock", "internal_test_access"}


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def normalize_promo_code(code: str) -> str:
    normalized = code.strip().upper()
    if not PROMO_CODE_PATTERN.match(normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid promo code format")
    return normalized


def _validate_access_type(access_type: str) -> str:
    if access_type not in ALLOWED_ACCESS_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported promo access_type")
    return access_type


def _validate_subscription_tier(subscription_tier_granted: str | None) -> str | None:
    if subscription_tier_granted is None:
        return None
    if subscription_tier_granted not in {"free", "premium"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported subscription tier")
    return subscription_tier_granted


def _validate_duration_days(duration_days: int | None) -> int | None:
    if duration_days is None:
        return None
    if duration_days <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="duration_days must be greater than zero")
    return duration_days


def _validate_max_redemptions(max_redemptions: int | None) -> int | None:
    if max_redemptions is None:
        return None
    if max_redemptions <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="max_redemptions must be greater than zero")
    return max_redemptions


def _validate_access_configuration(
    *,
    access_type: str,
    subscription_tier_granted: str | None,
    duration_days: int | None,
) -> None:
    if access_type in {"temporary_premium", "gift_like_access", "internal_test_access"}:
        if subscription_tier_granted != "premium":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This promo access_type requires subscription_tier_granted='premium'",
            )
        if duration_days is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This promo access_type requires duration_days")


def _validate_window(*, starts_at: datetime | None, ends_at: datetime | None) -> tuple[datetime | None, datetime | None]:
    normalized_start = _normalize_datetime(starts_at) if starts_at is not None else None
    normalized_end = _normalize_datetime(ends_at) if ends_at is not None else None
    if normalized_start is not None and normalized_end is not None and normalized_end <= normalized_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code ends_at must be after starts_at")
    return normalized_start, normalized_end


def get_promo_code_or_404(session: Session, *, code_id: int) -> PromoAccessCode:
    promo_code = session.get(PromoAccessCode, code_id)
    if promo_code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found")
    return promo_code


def list_promo_codes(session: Session, *, limit: int = 100) -> list[PromoAccessCode]:
    statement = select(PromoAccessCode).order_by(PromoAccessCode.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())


def list_promo_redemptions(
    session: Session,
    *,
    limit: int = 100,
    promo_access_code_id: int | None = None,
    user_id: int | None = None,
) -> list[PromoAccessRedemption]:
    statement = select(PromoAccessRedemption).order_by(PromoAccessRedemption.redeemed_at.desc()).limit(limit)
    if promo_access_code_id is not None:
        statement = statement.where(PromoAccessRedemption.promo_access_code_id == promo_access_code_id)
    if user_id is not None:
        statement = statement.where(PromoAccessRedemption.user_id == user_id)
    return list(session.exec(statement).all())


def list_redemptions_for_user(session: Session, *, user_id: int) -> list[PromoAccessRedemption]:
    statement = (
        select(PromoAccessRedemption)
        .where(PromoAccessRedemption.user_id == user_id)
        .order_by(PromoAccessRedemption.redeemed_at.desc())
    )
    return list(session.exec(statement).all())


def create_promo_code(session: Session, *, payload: PromoAccessCodeCreate) -> PromoAccessCode:
    normalized_code = normalize_promo_code(payload.code)
    if session.exec(select(PromoAccessCode).where(PromoAccessCode.key == payload.key)).first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code key already exists")
    if session.exec(select(PromoAccessCode).where(PromoAccessCode.code == normalized_code)).first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code value already exists")
    access_type = _validate_access_type(payload.access_type)
    subscription_tier_granted = _validate_subscription_tier(payload.subscription_tier_granted)
    duration_days = _validate_duration_days(payload.duration_days)
    max_redemptions = _validate_max_redemptions(payload.max_redemptions)
    _validate_access_configuration(
        access_type=access_type,
        subscription_tier_granted=subscription_tier_granted,
        duration_days=duration_days,
    )
    starts_at, ends_at = _validate_window(starts_at=payload.starts_at, ends_at=payload.ends_at)
    promo_code = PromoAccessCode(
        key=payload.key,
        name=payload.name,
        code=normalized_code,
        partner_name=payload.partner_name,
        access_type=access_type,
        subscription_tier_granted=subscription_tier_granted,
        duration_days=duration_days,
        max_redemptions=max_redemptions,
        redemption_count=0,
        starts_at=starts_at,
        ends_at=ends_at,
        is_active=payload.is_active,
    )
    return _persist(session, promo_code)


def update_promo_code(session: Session, *, promo_code: PromoAccessCode, payload: PromoAccessCodeUpdate) -> PromoAccessCode:
    update_data = payload.model_dump(exclude_unset=True)
    if "key" in update_data and update_data["key"] is not None and update_data["key"] != promo_code.key:
        if session.exec(select(PromoAccessCode).where(PromoAccessCode.key == update_data["key"])).first() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code key already exists")
    if "code" in update_data and update_data["code"] is not None:
        update_data["code"] = normalize_promo_code(update_data["code"])
        existing = session.exec(select(PromoAccessCode).where(PromoAccessCode.code == update_data["code"])).first()
        if existing is not None and existing.id != promo_code.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code value already exists")
    if "access_type" in update_data and update_data["access_type"] is not None:
        update_data["access_type"] = _validate_access_type(update_data["access_type"])
    if "subscription_tier_granted" in update_data:
        update_data["subscription_tier_granted"] = _validate_subscription_tier(update_data["subscription_tier_granted"])
    if "duration_days" in update_data:
        update_data["duration_days"] = _validate_duration_days(update_data["duration_days"])
    if "max_redemptions" in update_data:
        update_data["max_redemptions"] = _validate_max_redemptions(update_data["max_redemptions"])
    resolved_access_type = update_data.get("access_type") or promo_code.access_type
    resolved_tier = update_data.get("subscription_tier_granted", promo_code.subscription_tier_granted)
    resolved_duration = update_data.get("duration_days", promo_code.duration_days)
    _validate_access_configuration(
        access_type=resolved_access_type,
        subscription_tier_granted=resolved_tier,
        duration_days=resolved_duration,
    )
    starts_at = _normalize_datetime(update_data["starts_at"]) if update_data.get("starts_at") is not None else promo_code.starts_at
    ends_at = _normalize_datetime(update_data["ends_at"]) if update_data.get("ends_at") is not None else promo_code.ends_at
    starts_at, ends_at = _validate_window(starts_at=starts_at, ends_at=ends_at)
    update_data["starts_at"] = starts_at
    update_data["ends_at"] = ends_at
    for field_name, value in update_data.items():
        setattr(promo_code, field_name, value)
    promo_code.updated_at = utc_now()
    return _persist(session, promo_code)


def apply_promo_access_to_user(
    session: Session,
    *,
    user: User,
    subscription_tier_granted: str | None,
    duration_days: int | None,
) -> User:
    if subscription_tier_granted != "premium":
        return user
    if duration_days is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Premium promo codes require duration_days")
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


def _validate_redeemable(promo_code: PromoAccessCode) -> None:
    now = utc_now()
    if not promo_code.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code is inactive")
    if promo_code.starts_at is not None and promo_code.starts_at > now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code is not active yet")
    if promo_code.ends_at is not None and promo_code.ends_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code has expired")
    if promo_code.max_redemptions is not None and promo_code.redemption_count >= promo_code.max_redemptions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code redemption limit reached")


def redeem_promo_code(
    session: Session,
    *,
    current_user: User,
    code: str,
) -> tuple[PromoAccessCode, PromoAccessRedemption]:
    normalized_code = normalize_promo_code(code)
    promo_code = session.exec(select(PromoAccessCode).where(PromoAccessCode.code == normalized_code)).first()
    if promo_code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found")
    _validate_redeemable(promo_code)
    existing_redemption = session.exec(
        select(PromoAccessRedemption).where(
            PromoAccessRedemption.promo_access_code_id == promo_code.id,
            PromoAccessRedemption.user_id == current_user.id,
        )
    ).first()
    if existing_redemption is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already redeemed this promo code")

    expires_at: datetime | None = None
    if promo_code.access_type in {"temporary_premium", "gift_like_access", "internal_test_access"}:
        apply_promo_access_to_user(
            session,
            user=current_user,
            subscription_tier_granted=promo_code.subscription_tier_granted,
            duration_days=promo_code.duration_days,
        )
        session.refresh(current_user)
        expires_at = current_user.subscription_expires_at
    redemption = PromoAccessRedemption(
        promo_access_code_id=promo_code.id,
        user_id=current_user.id,
        redeemed_at=utc_now(),
        expires_at=expires_at,
    )
    promo_code.redemption_count += 1
    promo_code.updated_at = utc_now()
    session.add(promo_code)
    session.add(redemption)
    session.commit()
    session.refresh(promo_code)
    session.refresh(redemption)
    return promo_code, redemption


def generate_promo_code_value(session: Session, *, length: int = 10) -> str:
    for _attempt in range(25):
        candidate = "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))
        if session.exec(select(PromoAccessCode).where(PromoAccessCode.code == candidate)).first() is None:
            return candidate
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate promo code")
