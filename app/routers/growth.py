from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.growth_schema import (
    GiftSubscriptionCreate,
    GiftSubscriptionRead,
    GiftSubscriptionRedeemRequest,
    GiftSubscriptionRedeemResponse,
    ReferralAttributionRead,
    ReferralSummaryResponse,
)
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.growth_service import (
    create_gift_subscription,
    get_or_create_referral_code,
    get_referral_summary,
    list_gifts_for_admin,
    list_gifts_for_purchaser,
    list_referral_attributions,
    redeem_gift_subscription,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/growth", tags=["growth"])
admin_router = APIRouter(prefix="/admin/growth", tags=["growth-admin"])


@router.get("/referral/me", response_model=ReferralSummaryResponse, summary="Get my referral code and stats")
def get_my_referral_summary(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReferralSummaryResponse:
    referral_code, created = get_or_create_referral_code(session, user=current_user)
    if created:
        create_audit_log(
            session,
            action_type="referral_code_created",
            entity_type="referral_code",
            entity_id=str(referral_code.id),
            summary=f"Created referral code for user {current_user.email}",
            actor_user=current_user,
            request_id=get_request_id_from_request(request),
            metadata={"code": referral_code.code},
        )
    track_event_safe(
        session,
        event_name="referral_code_viewed",
        user=current_user,
        metadata={"code": referral_code.code},
    )
    _referral_code, total_referrals, premium_conversions = get_referral_summary(session, user=current_user)
    return ReferralSummaryResponse(
        referral_code=referral_code,
        total_referrals=total_referrals,
        premium_conversions=premium_conversions,
    )


@router.post("/gifts", response_model=GiftSubscriptionRead, status_code=status.HTTP_201_CREATED, summary="Create a gift")
def create_my_gift(
    payload: GiftSubscriptionCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> GiftSubscriptionRead:
    gift = create_gift_subscription(
        session,
        purchaser_user=current_user,
        duration_days=payload.duration_days,
        notes=payload.notes,
    )
    create_audit_log(
        session,
        action_type="gift_subscription_created",
        entity_type="gift_subscription",
        entity_id=str(gift.id),
        summary=f"Created gift subscription for purchaser {current_user.email}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"code": gift.code, "duration_days": gift.duration_days},
    )
    track_event_safe(
        session,
        event_name="gift_subscription_created",
        user=current_user,
        metadata={"gift_id": gift.id, "duration_days": gift.duration_days},
    )
    return gift


@router.get("/gifts/me", response_model=list[GiftSubscriptionRead], summary="List gifts created by me")
def list_my_gifts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[GiftSubscriptionRead]:
    return list_gifts_for_purchaser(session, purchaser_user_id=current_user.id)


@router.post("/gifts/redeem", response_model=GiftSubscriptionRedeemResponse, summary="Redeem a gift code")
def redeem_my_gift(
    payload: GiftSubscriptionRedeemRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> GiftSubscriptionRedeemResponse:
    gift = redeem_gift_subscription(session, current_user=current_user, code=payload.code)
    create_audit_log(
        session,
        action_type="gift_subscription_redeemed",
        entity_type="gift_subscription",
        entity_id=str(gift.id),
        summary=f"Redeemed gift subscription for user {current_user.email}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"code": gift.code, "duration_days": gift.duration_days},
    )
    track_event_safe(
        session,
        event_name="gift_subscription_redeemed",
        user=current_user,
        metadata={"gift_id": gift.id, "duration_days": gift.duration_days},
    )
    session.refresh(current_user)
    return GiftSubscriptionRedeemResponse(
        gift=gift,
        subscription_status=current_user.subscription_status,
        subscription_tier=current_user.subscription_tier,
        expires_at=current_user.subscription_expires_at,
    )


@admin_router.get("/referrals", response_model=list[ReferralAttributionRead], summary="List referral attributions")
def list_referrals_admin(
    referrer_user_id: int | None = Query(default=None),
    referred_user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[ReferralAttributionRead]:
    return list_referral_attributions(
        session,
        referrer_user_id=referrer_user_id,
        referred_user_id=referred_user_id,
        limit=limit,
    )


@admin_router.get("/gifts", response_model=list[GiftSubscriptionRead], summary="List gift subscriptions")
def list_gifts_admin(
    status_value: str | None = Query(default=None, alias="status"),
    purchaser_user_id: int | None = Query(default=None),
    recipient_user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[GiftSubscriptionRead]:
    return list_gifts_for_admin(
        session,
        status_value=status_value,
        purchaser_user_id=purchaser_user_id,
        recipient_user_id=recipient_user_id,
        limit=limit,
    )
