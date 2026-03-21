from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.subscription_schema import ReaderAccessResponse, SubscriptionAdminUpdate, SubscriptionStatusRead
from app.services.audit_service import create_audit_log
from app.services.reader_service import get_published_book_or_404
from app.services.subscription_service import (
    activate_premium,
    apply_subscription_admin_update,
    build_subscription_status_read,
    get_reader_access_for_user,
    get_user_or_404,
    grant_trial,
    revoke_premium,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/me", response_model=SubscriptionStatusRead, summary="Get current subscription state")
def get_my_subscription(current_user: User = Depends(get_current_active_user)) -> SubscriptionStatusRead:
    return build_subscription_status_read(current_user)


@router.get(
    "/me/access/books/{book_id}",
    response_model=ReaderAccessResponse,
    summary="Get current reader access for a book",
)
def get_my_book_access(
    book_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReaderAccessResponse:
    get_published_book_or_404(session, book_id)
    return get_reader_access_for_user(current_user, book_id)


@router.patch(
    "/users/{user_id}",
    response_model=SubscriptionStatusRead,
    summary="Update subscription fields for a user",
)
def update_user_subscription(
    user_id: int,
    payload: SubscriptionAdminUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> SubscriptionStatusRead:
    user = get_user_or_404(session, user_id)
    updated_user = apply_subscription_admin_update(session, user=user, payload=payload)
    create_audit_log(
        session,
        action_type="subscription_updated",
        entity_type="user_subscription",
        entity_id=str(updated_user.id),
        summary=f"Updated subscription for user {updated_user.email}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return build_subscription_status_read(updated_user)


@router.post(
    "/users/{user_id}/grant-trial",
    response_model=SubscriptionStatusRead,
    summary="Grant a premium trial to a user",
)
def grant_user_trial(
    user_id: int,
    request: Request,
    days: int = Query(default=7, ge=1, le=60),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> SubscriptionStatusRead:
    user = get_user_or_404(session, user_id)
    updated_user = grant_trial(session, user=user, days=days)
    create_audit_log(
        session,
        action_type="subscription_trial_granted",
        entity_type="user_subscription",
        entity_id=str(updated_user.id),
        summary=f"Granted premium trial to user {updated_user.email}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"days": days},
    )
    return build_subscription_status_read(updated_user)


@router.post(
    "/users/{user_id}/activate-premium",
    response_model=SubscriptionStatusRead,
    summary="Activate premium access for a user",
)
def activate_user_premium(
    user_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> SubscriptionStatusRead:
    user = get_user_or_404(session, user_id)
    updated_user = activate_premium(session, user=user)
    create_audit_log(
        session,
        action_type="subscription_premium_activated",
        entity_type="user_subscription",
        entity_id=str(updated_user.id),
        summary=f"Activated premium access for user {updated_user.email}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"subscription_status": updated_user.subscription_status},
    )
    return build_subscription_status_read(updated_user)


@router.post(
    "/users/{user_id}/revoke-premium",
    response_model=SubscriptionStatusRead,
    summary="Revoke premium access for a user",
)
def revoke_user_premium(
    user_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> SubscriptionStatusRead:
    user = get_user_or_404(session, user_id)
    updated_user = revoke_premium(session, user=user)
    create_audit_log(
        session,
        action_type="subscription_revoked",
        entity_type="user_subscription",
        entity_id=str(updated_user.id),
        summary=f"Revoked premium access for user {updated_user.email}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"subscription_status": updated_user.subscription_status},
    )
    return build_subscription_status_read(updated_user)
