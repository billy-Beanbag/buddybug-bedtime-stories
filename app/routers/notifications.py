from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.notification_schema import (
    DailyStorySuggestionResponse,
    NotificationEventCreate,
    NotificationEventRead,
    NotificationEventUpdate,
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
    NotificationQueueResponse,
)
from app.services.audit_service import create_audit_log
from app.services.analytics_service import track_event_safe
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.notification_service import (
    create_notification_event,
    generate_daily_story_suggestion,
    get_notification_or_404,
    get_or_create_notification_preference,
    list_notifications_for_user,
    mark_all_notifications_read,
    update_notification_event,
    update_notification_preference,
)
from app.services.user_service import get_user_by_id
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/notifications", tags=["notifications"])
admin_router = APIRouter(prefix="/admin/notifications", tags=["admin-notifications"])


@router.get("/preferences/me", response_model=NotificationPreferenceRead, summary="Get current user notification preferences")
def get_my_notification_preferences(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> NotificationPreferenceRead:
    return get_or_create_notification_preference(session, user_id=current_user.id)


@router.patch("/preferences/me", response_model=NotificationPreferenceRead, summary="Update current user notification preferences")
def patch_my_notification_preferences(
    payload: NotificationPreferenceUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> NotificationPreferenceRead:
    preference = get_or_create_notification_preference(session, user_id=current_user.id)
    updated = update_notification_preference(session, preference=preference, **payload.model_dump(exclude_unset=True))
    create_audit_log(
        session,
        action_type="notification_preferences_updated",
        entity_type="notification_preference",
        entity_id=str(updated.id),
        summary=f"Updated notification preferences for user {current_user.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@router.get("/me", response_model=NotificationQueueResponse, summary="List current user notifications")
def get_my_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> NotificationQueueResponse:
    items = list_notifications_for_user(session, user_id=current_user.id, unread_only=unread_only, limit=limit)
    return NotificationQueueResponse(items=[NotificationEventRead.model_validate(item) for item in items])


@router.patch("/me/{notification_id}", response_model=NotificationEventRead, summary="Update one current user notification")
def patch_my_notification(
    notification_id: int,
    payload: NotificationEventUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> NotificationEventRead:
    event = get_notification_or_404(session, notification_id=notification_id)
    if event.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    updated = update_notification_event(session, event=event, **payload.model_dump(exclude_unset=True))
    if payload.is_read:
        track_event_safe(
            session,
            event_name="notification_read",
            user=current_user,
            child_profile_id=updated.child_profile_id,
            metadata={"notification_id": updated.id, "notification_type": updated.notification_type},
        )
    return updated


@router.post("/me/mark-all-read", summary="Mark all current user notifications read")
def mark_my_notifications_read(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    updated_count = mark_all_notifications_read(session, user_id=current_user.id)
    if updated_count:
        track_event_safe(
            session,
            event_name="notification_read",
            user=current_user,
            metadata={"mark_all": True, "updated_count": updated_count},
        )
    return {"ok": True, "updated_count": updated_count}


@router.get("/me/daily-story", response_model=DailyStorySuggestionResponse, summary="Get or lazily generate today's story suggestion")
def get_my_daily_story(
    child_profile_id: int | None = Query(default=None),
    date_value: date | None = Query(default=None, alias="date"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> DailyStorySuggestionResponse:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    return generate_daily_story_suggestion(
        session,
        user=current_user,
        child_profile_id=child_profile_id,
        target_date=date_value,
    )


@router.post("/me/daily-story/generate", response_model=DailyStorySuggestionResponse, summary="Generate or return a daily story suggestion")
def generate_my_daily_story(
    request: Request,
    child_profile_id: int | None = Query(default=None),
    date_value: date | None = Query(default=None, alias="date"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> DailyStorySuggestionResponse:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    result = generate_daily_story_suggestion(
        session,
        user=current_user,
        child_profile_id=child_profile_id,
        target_date=date_value,
    )
    if result.suggestion is not None:
        create_audit_log(
            session,
            action_type="daily_story_generated",
            entity_type="daily_story_suggestion",
            entity_id=str(result.suggestion.id),
            summary=f"Generated daily story for user {current_user.id}",
            actor_user=current_user,
            request_id=get_request_id_from_request(request),
            metadata={"child_profile_id": child_profile_id, "date": str(date_value or result.suggestion.suggestion_date)},
        )
    return result


@admin_router.post("/users/{user_id}/create", response_model=NotificationEventRead, summary="Admin create a notification event")
def admin_create_notification(
    user_id: int,
    payload: NotificationEventCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> NotificationEventRead:
    target_user = get_user_by_id(session, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.child_profile_id is not None:
        validate_child_profile_ownership(session, user_id=target_user.id, child_profile_id=payload.child_profile_id)
    event = create_notification_event(
        session,
        user_id=target_user.id,
        child_profile_id=payload.child_profile_id,
        notification_type=payload.notification_type,
        delivery_channel=payload.delivery_channel,
        title=payload.title,
        body=payload.body,
        metadata_json=payload.metadata_json,
        scheduled_for=payload.scheduled_for,
    )
    create_audit_log(
        session,
        action_type="notification_event_created_manual",
        entity_type="notification_event",
        entity_id=str(event.id),
        summary=f"Created manual notification for user {target_user.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(),
    )
    return event


@admin_router.get("/users/{user_id}", response_model=NotificationQueueResponse, summary="Admin list notifications for one user")
def admin_list_user_notifications(
    user_id: int,
    unread_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> NotificationQueueResponse:
    target_user = get_user_by_id(session, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    items = list_notifications_for_user(session, user_id=target_user.id, unread_only=unread_only, limit=limit)
    return NotificationQueueResponse(items=[NotificationEventRead.model_validate(item) for item in items])
