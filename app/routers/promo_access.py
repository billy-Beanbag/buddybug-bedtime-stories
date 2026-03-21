from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.promo_access_schema import (
    PromoAccessCodeCreate,
    PromoAccessCodeRead,
    PromoAccessCodeUpdate,
    PromoAccessRedeemRequest,
    PromoAccessRedeemResponse,
    PromoAccessRedemptionRead,
)
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.promo_access_service import (
    create_promo_code,
    get_promo_code_or_404,
    list_promo_codes,
    list_promo_redemptions,
    list_redemptions_for_user,
    redeem_promo_code,
    update_promo_code,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/promo", tags=["promo"])
admin_router = APIRouter(prefix="/admin/promo", tags=["promo-admin"])


@router.post("/redeem", response_model=PromoAccessRedeemResponse, summary="Redeem promo access code")
def redeem_my_promo(
    payload: PromoAccessRedeemRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> PromoAccessRedeemResponse:
    try:
        promo_code, redemption = redeem_promo_code(session, current_user=current_user, code=payload.code)
    except Exception as exc:
        detail = getattr(exc, "detail", "Promo code redemption failed")
        track_event_safe(
            session,
            event_name="promo_code_failed",
            user=current_user,
            metadata={"code": payload.code.strip().upper(), "detail": detail},
        )
        raise
    create_audit_log(
        session,
        action_type="promo_code_redeemed",
        entity_type="promo_access_redemption",
        entity_id=str(redemption.id),
        summary=f"Redeemed promo code '{promo_code.name}' for user {current_user.email}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"promo_code_id": promo_code.id, "code": promo_code.code, "partner_name": promo_code.partner_name},
    )
    track_event_safe(
        session,
        event_name="promo_code_redeemed",
        user=current_user,
        metadata={"promo_code_id": promo_code.id, "access_type": promo_code.access_type, "partner_name": promo_code.partner_name},
    )
    session.refresh(current_user)
    return PromoAccessRedeemResponse(
        code=promo_code,
        redemption=redemption,
        subscription_status=current_user.subscription_status,
        subscription_tier=current_user.subscription_tier,
        expires_at=current_user.subscription_expires_at,
    )


@router.get("/me/redemptions", response_model=list[PromoAccessRedemptionRead], summary="List my promo redemptions")
def list_my_redemptions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[PromoAccessRedemptionRead]:
    return list_redemptions_for_user(session, user_id=current_user.id)


@admin_router.get("/codes", response_model=list[PromoAccessCodeRead], summary="List promo codes")
def list_codes_admin(
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[PromoAccessCodeRead]:
    return list_promo_codes(session, limit=limit)


@admin_router.post("/codes", response_model=PromoAccessCodeRead, status_code=status.HTTP_201_CREATED, summary="Create promo code")
def create_code_admin(
    payload: PromoAccessCodeCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> PromoAccessCodeRead:
    promo_code = create_promo_code(session, payload=payload)
    create_audit_log(
        session,
        action_type="promo_code_created",
        entity_type="promo_access_code",
        entity_id=str(promo_code.id),
        summary=f"Created promo code '{promo_code.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"key": promo_code.key, "code": promo_code.code, "partner_name": promo_code.partner_name},
    )
    return promo_code


@admin_router.patch("/codes/{code_id}", response_model=PromoAccessCodeRead, summary="Update promo code")
def patch_code_admin(
    code_id: int,
    payload: PromoAccessCodeUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> PromoAccessCodeRead:
    promo_code = get_promo_code_or_404(session, code_id=code_id)
    updated = update_promo_code(session, promo_code=promo_code, payload=payload)
    create_audit_log(
        session,
        action_type="promo_code_updated",
        entity_type="promo_access_code",
        entity_id=str(updated.id),
        summary=f"Updated promo code '{updated.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@admin_router.get("/redemptions", response_model=list[PromoAccessRedemptionRead], summary="List promo redemptions")
def list_redemptions_admin(
    promo_access_code_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[PromoAccessRedemptionRead]:
    return list_promo_redemptions(
        session,
        limit=limit,
        promo_access_code_id=promo_access_code_id,
        user_id=user_id,
    )
