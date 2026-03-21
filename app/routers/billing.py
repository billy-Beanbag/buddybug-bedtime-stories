from fastapi import APIRouter, Depends, Header, Request
from sqlmodel import Session

from app.config import BILLING_RATE_LIMIT_PER_MINUTE
from app.database import get_session
from app.middleware.rate_limit import create_rate_limit_dependency
from app.models import User
from app.schemas.billing_schema import (
    BillingPortalResponse,
    BillingStatusResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    StripeWebhookAck,
)
from app.services.analytics_service import track_event_safe
from app.services.billing_service import (
    build_billing_status_response,
    construct_stripe_event,
    create_billing_portal_session,
    create_checkout_session,
    handle_stripe_event,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/billing", tags=["billing"])
billing_rate_limit = create_rate_limit_dependency(limit=BILLING_RATE_LIMIT_PER_MINUTE, scope_key="billing")


@router.post(
    "/checkout",
    response_model=CheckoutSessionResponse,
    summary="Create a Stripe checkout session",
    dependencies=[Depends(billing_rate_limit)],
)
def start_checkout(
    payload: CheckoutSessionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> CheckoutSessionResponse:
    checkout_url, session_id = create_checkout_session(
        session,
        user=current_user,
        price_key=payload.price_key,
        success_path=payload.success_path,
        cancel_path=payload.cancel_path,
    )
    track_event_safe(
        session,
        event_name="checkout_started",
        user=current_user,
        session_id=session_id,
        metadata={"price_key": payload.price_key, "source": "backend_billing_checkout"},
    )
    return CheckoutSessionResponse(checkout_url=checkout_url, session_id=session_id)


@router.post(
    "/portal",
    response_model=BillingPortalResponse,
    summary="Create a Stripe billing portal session",
    dependencies=[Depends(billing_rate_limit)],
)
def open_billing_portal(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BillingPortalResponse:
    portal_url = create_billing_portal_session(session, user=current_user)
    track_event_safe(
        session,
        event_name="billing_portal_opened",
        user=current_user,
        metadata={"source": "backend_billing_portal"},
    )
    return BillingPortalResponse(portal_url=portal_url)


@router.get("/me", response_model=BillingStatusResponse, summary="Get current billing status")
def get_my_billing_status(current_user: User = Depends(get_current_active_user)) -> BillingStatusResponse:
    return build_billing_status_response(current_user)


@router.post(
    "/webhook",
    response_model=StripeWebhookAck,
    summary="Process Stripe webhook events",
    dependencies=[Depends(billing_rate_limit)],
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
    session: Session = Depends(get_session),
) -> StripeWebhookAck:
    payload = await request.body()
    event = construct_stripe_event(payload, stripe_signature)
    handle_stripe_event(session, event)
    return StripeWebhookAck(received=True)
