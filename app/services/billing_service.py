import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import stripe
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.config import (
    STRIPE_CANCEL_URL,
    STRIPE_PRICE_ID_PREMIUM_MONTHLY,
    STRIPE_SECRET_KEY,
    STRIPE_SUCCESS_URL,
    STRIPE_WEBHOOK_SECRET,
)
from app.models import User
from app.schemas.billing_schema import BillingStatusResponse
from app.services.analytics_service import track_event_safe
from app.services.billing_recovery_service import sync_recovery_from_subscription_state
from app.services.growth_service import mark_referral_premium_conversion
from app.services.review_service import utc_now
from app.services.subscription_service import has_premium_access

logger = logging.getLogger(__name__)

stripe.api_key = STRIPE_SECRET_KEY

PRICE_KEY_MAP = {
    "premium_monthly": STRIPE_PRICE_ID_PREMIUM_MONTHLY,
}
STRIPE_TO_LOCAL_STATUS_MAP = {
    "trialing": "trialing",
    "active": "active",
    "past_due": "past_due",
    "canceled": "canceled",
    "unpaid": "expired",
    "incomplete": "none",
    "incomplete_expired": "expired",
}


def _require_stripe_api_key() -> None:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stripe is not configured")
    stripe.api_key = STRIPE_SECRET_KEY


def _require_stripe_webhook_secret() -> str:
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe webhook secret is not configured",
        )
    return STRIPE_WEBHOOK_SECRET


def _require_checkout_urls() -> tuple[str, str]:
    if not STRIPE_SUCCESS_URL or not STRIPE_CANCEL_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe success/cancel URLs are not configured",
        )
    return STRIPE_SUCCESS_URL, STRIPE_CANCEL_URL


def _resolve_checkout_url(base_url: str, override_path: str | None) -> str:
    if not override_path:
        return base_url
    if not override_path.startswith("/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Checkout return path must start with '/'")

    parsed_base = urlsplit(base_url)
    parsed_override = urlsplit(override_path)
    return urlunsplit(
        (
            parsed_base.scheme,
            parsed_base.netloc,
            parsed_override.path or parsed_base.path,
            parsed_override.query,
            parsed_override.fragment,
        )
    )


def _get_price_id_for_key(price_key: str) -> str:
    if price_key not in PRICE_KEY_MAP:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported price key")
    price_id = PRICE_KEY_MAP[price_key]
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe price ID is not configured",
        )
    return price_id


def _extract_value(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _timestamp_to_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    return datetime.fromtimestamp(int(value), tz=timezone.utc)


def _local_status_from_stripe_status(stripe_status: str | None) -> str:
    if stripe_status is None:
        return "none"
    return STRIPE_TO_LOCAL_STATUS_MAP.get(stripe_status, "none")


def _subscription_tier_for_status(local_status: str) -> str:
    if local_status in {"active", "trialing"}:
        return "premium"
    return "free"


def _persist_user(session: Session, user: User) -> User:
    user.updated_at = utc_now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_stripe_customer_id(session: Session, stripe_customer_id: str) -> User | None:
    statement = select(User).where(User.stripe_customer_id == stripe_customer_id)
    return session.exec(statement).first()


def build_billing_status_response(user: User) -> BillingStatusResponse:
    return BillingStatusResponse(
        user_id=user.id,
        subscription_tier=user.subscription_tier,
        subscription_status=user.subscription_status,
        stripe_customer_id=user.stripe_customer_id,
        stripe_subscription_id=user.stripe_subscription_id,
        subscription_expires_at=user.subscription_expires_at,
        trial_ends_at=user.trial_ends_at,
        has_premium_access=has_premium_access(user),
    )


def get_or_create_stripe_customer(session: Session, *, user: User) -> str:
    _require_stripe_api_key()
    if user.stripe_customer_id:
        return user.stripe_customer_id

    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.display_name or None,
            metadata={"user_id": str(user.id), "user_email": user.email},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create Stripe customer",
        ) from exc

    user.stripe_customer_id = customer.id
    _persist_user(session, user)
    return customer.id


def create_checkout_session(
    session: Session,
    *,
    user: User,
    price_key: str,
    success_path: str | None = None,
    cancel_path: str | None = None,
) -> tuple[str, str]:
    _require_stripe_api_key()
    default_success_url, default_cancel_url = _require_checkout_urls()
    success_url = _resolve_checkout_url(default_success_url, success_path)
    cancel_url = _resolve_checkout_url(default_cancel_url, cancel_path)
    customer_id = get_or_create_stripe_customer(session, user=user)
    price_id = _get_price_id_for_key(price_key)
    metadata = {"user_id": str(user.id), "user_email": user.email}

    try:
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            client_reference_id=str(user.id),
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            subscription_data={"metadata": metadata},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create Stripe checkout session",
        ) from exc

    checkout_url = _extract_value(checkout_session, "url")
    session_id = _extract_value(checkout_session, "id")
    if not checkout_url or not session_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe checkout session was incomplete",
        )
    return checkout_url, session_id


def create_billing_portal_session(session: Session, *, user: User) -> str:
    _require_stripe_api_key()
    customer_id = get_or_create_stripe_customer(session, user=user)
    return_url = STRIPE_SUCCESS_URL or STRIPE_CANCEL_URL
    if not return_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe portal return URL is not configured",
        )

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create Stripe billing portal session",
        ) from exc

    portal_url = _extract_value(portal_session, "url")
    if not portal_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe billing portal session was incomplete",
        )
    return portal_url


def sync_user_subscription_from_stripe_subscription(
    session: Session,
    *,
    user: User,
    stripe_subscription: Any,
) -> User:
    stripe_status = _extract_value(stripe_subscription, "status")
    local_status = _local_status_from_stripe_status(stripe_status)
    customer_id = _extract_value(stripe_subscription, "customer")
    subscription_id = _extract_value(stripe_subscription, "id")

    if customer_id:
        user.stripe_customer_id = str(customer_id)
    if subscription_id:
        user.stripe_subscription_id = str(subscription_id)

    user.subscription_status = local_status
    user.subscription_tier = _subscription_tier_for_status(local_status)
    user.subscription_expires_at = _timestamp_to_datetime(
        _extract_value(stripe_subscription, "current_period_end")
    )
    user.trial_ends_at = _timestamp_to_datetime(_extract_value(stripe_subscription, "trial_end"))
    persisted_user = _persist_user(session, user)
    attribution = mark_referral_premium_conversion(session, user=persisted_user)
    if attribution is not None and attribution.premium_converted_at is not None:
        track_event_safe(
            session,
            event_name="referral_premium_converted",
            user=persisted_user,
            metadata={"referrer_user_id": attribution.referrer_user_id},
        )
    sync_recovery_from_subscription_state(
        session,
        user=persisted_user,
        source_type="stripe_webhook",
        external_reference=str(subscription_id) if subscription_id else user.stripe_subscription_id,
    )
    return persisted_user


def _find_user_from_metadata_or_customer(
    session: Session,
    *,
    metadata: Any = None,
    stripe_customer_id: str | None = None,
) -> User | None:
    metadata_user_id = None
    if metadata is not None:
        metadata_user_id = _extract_value(metadata, "user_id")
        if metadata_user_id is None and isinstance(metadata, dict):
            metadata_user_id = metadata.get("user_id")

    if metadata_user_id is not None:
        try:
            user = session.get(User, int(metadata_user_id))
        except (TypeError, ValueError):
            user = None
        if user is not None:
            return user

    if stripe_customer_id:
        return get_user_by_stripe_customer_id(session, str(stripe_customer_id))

    return None


def handle_checkout_session_completed(session: Session, stripe_checkout_session: Any) -> User | None:
    metadata = _extract_value(stripe_checkout_session, "metadata")
    stripe_customer_id = _extract_value(stripe_checkout_session, "customer")
    user = _find_user_from_metadata_or_customer(
        session,
        metadata=metadata,
        stripe_customer_id=stripe_customer_id,
    )
    if user is None:
        logger.warning("Stripe checkout completed for unknown user")
        return None

    if stripe_customer_id:
        user.stripe_customer_id = str(stripe_customer_id)

    subscription_id = _extract_value(stripe_checkout_session, "subscription")
    if subscription_id:
        user.stripe_subscription_id = str(subscription_id)
        _persist_user(session, user)
        try:
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        except Exception as exc:
            logger.warning("Unable to retrieve Stripe subscription %s: %s", subscription_id, exc)
            persisted_user = user
            track_event_safe(
                session,
                event_name="checkout_completed",
                user=persisted_user,
                session_id=str(_extract_value(stripe_checkout_session, "id") or ""),
                metadata={
                    "source": "stripe_webhook",
                    "stripe_customer_id": persisted_user.stripe_customer_id,
                    "stripe_subscription_id": persisted_user.stripe_subscription_id,
                },
            )
            return persisted_user
        persisted_user = sync_user_subscription_from_stripe_subscription(
            session,
            user=user,
            stripe_subscription=stripe_subscription,
        )
        track_event_safe(
            session,
            event_name="checkout_completed",
            user=persisted_user,
            session_id=str(_extract_value(stripe_checkout_session, "id") or ""),
            metadata={
                "source": "stripe_webhook",
                "stripe_customer_id": persisted_user.stripe_customer_id,
                "stripe_subscription_id": persisted_user.stripe_subscription_id,
            },
        )
        return persisted_user

    persisted_user = _persist_user(session, user)
    track_event_safe(
        session,
        event_name="checkout_completed",
        user=persisted_user,
        session_id=str(_extract_value(stripe_checkout_session, "id") or ""),
        metadata={
            "source": "stripe_webhook",
            "stripe_customer_id": persisted_user.stripe_customer_id,
            "stripe_subscription_id": persisted_user.stripe_subscription_id,
        },
    )
    return persisted_user


def handle_customer_subscription_updated(session: Session, stripe_subscription: Any) -> User | None:
    stripe_customer_id = _extract_value(stripe_subscription, "customer")
    metadata = _extract_value(stripe_subscription, "metadata")
    user = _find_user_from_metadata_or_customer(
        session,
        metadata=metadata,
        stripe_customer_id=stripe_customer_id,
    )
    if user is None:
        logger.warning("Stripe subscription update for unknown customer %s", stripe_customer_id)
        return None
    return sync_user_subscription_from_stripe_subscription(
        session,
        user=user,
        stripe_subscription=stripe_subscription,
    )


def handle_customer_subscription_deleted(session: Session, stripe_subscription: Any) -> User | None:
    return handle_customer_subscription_updated(session, stripe_subscription)


def construct_stripe_event(payload: bytes, stripe_signature: str | None) -> Any:
    _require_stripe_api_key()
    webhook_secret = _require_stripe_webhook_secret()
    if not stripe_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature")

    try:
        return stripe.Webhook.construct_event(payload=payload, sig_header=stripe_signature, secret=webhook_secret)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe webhook") from exc


def handle_stripe_event(session: Session, event: Any) -> None:
    event_type = _extract_value(event, "type")
    event_data = _extract_value(_extract_value(event, "data", {}), "object")

    if event_type == "checkout.session.completed":
        handle_checkout_session_completed(session, event_data)
        return
    if event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        handle_customer_subscription_updated(session, event_data)
        return
    if event_type == "customer.subscription.deleted":
        handle_customer_subscription_deleted(session, event_data)
