from __future__ import annotations

import json
from datetime import date, datetime, time

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    Book,
    ChildProfile,
    DailyStorySuggestion,
    NotificationEvent,
    NotificationPreference,
    User,
)
from app.schemas.notification_schema import DailyStorySuggestionResponse
from app.services.analytics_service import track_event_safe
from app.services.bedtime_pack_service import get_existing_pack_story_candidate
from app.services.child_profile_service import get_child_profile_for_user
from app.services.i18n_service import get_book_translation, normalize_language
from app.services.parental_controls_service import resolve_parental_controls
from app.services.reading_plan_service import get_plan_story_candidate
from app.services.recommendation_service import get_personalized_recommendations_for_user
from app.services.review_service import utc_now

ALLOWED_NOTIFICATION_TYPES = {
    "bedtime_reminder",
    "new_story_recommendation",
    "saved_story_ready",
    "premium_expiring_soon",
    "weekly_digest_placeholder",
}
ALLOWED_DELIVERY_CHANNELS = {"in_app", "email_placeholder"}


def _validate_notification_type(notification_type: str) -> str:
    if notification_type not in ALLOWED_NOTIFICATION_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported notification type")
    return notification_type


def _validate_delivery_channel(delivery_channel: str) -> str:
    if delivery_channel not in ALLOWED_DELIVERY_CHANNELS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported notification channel")
    return delivery_channel


def _validate_quiet_hour(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid quiet hours value: {exc}")
    return value


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def get_or_create_notification_preference(session: Session, *, user_id: int) -> NotificationPreference:
    preference = session.exec(select(NotificationPreference).where(NotificationPreference.user_id == user_id)).first()
    if preference is None:
        preference = NotificationPreference(user_id=user_id)
        preference = _persist(session, preference)
    return preference


def update_notification_preference(
    session: Session,
    *,
    preference: NotificationPreference,
    enable_in_app: bool | None = None,
    enable_email_placeholder: bool | None = None,
    enable_bedtime_reminders: bool | None = None,
    enable_new_story_alerts: bool | None = None,
    enable_weekly_digest: bool | None = None,
    quiet_hours_start: str | None = None,
    quiet_hours_end: str | None = None,
    timezone: str | None = None,
) -> NotificationPreference:
    if enable_in_app is not None:
        preference.enable_in_app = enable_in_app
    if enable_email_placeholder is not None:
        preference.enable_email_placeholder = enable_email_placeholder
    if enable_bedtime_reminders is not None:
        preference.enable_bedtime_reminders = enable_bedtime_reminders
    if enable_new_story_alerts is not None:
        preference.enable_new_story_alerts = enable_new_story_alerts
    if enable_weekly_digest is not None:
        preference.enable_weekly_digest = enable_weekly_digest
    if quiet_hours_start is not None:
        preference.quiet_hours_start = _validate_quiet_hour(quiet_hours_start)
    if quiet_hours_end is not None:
        preference.quiet_hours_end = _validate_quiet_hour(quiet_hours_end)
    if timezone is not None:
        preference.timezone = timezone
    preference.updated_at = utc_now()
    return _persist(session, preference)


def create_notification_event(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
    notification_type: str,
    delivery_channel: str,
    title: str,
    body: str,
    metadata: dict[str, object] | None = None,
    metadata_json: str | None = None,
    delivered: bool = False,
    scheduled_for: datetime | None = None,
    delivered_at: datetime | None = None,
) -> NotificationEvent:
    if metadata_json is None and metadata is not None:
        metadata_json = json.dumps(metadata, default=str, sort_keys=True)
    event = NotificationEvent(
        user_id=user_id,
        child_profile_id=child_profile_id,
        notification_type=_validate_notification_type(notification_type),
        delivery_channel=_validate_delivery_channel(delivery_channel),
        title=title,
        body=body,
        metadata_json=metadata_json,
        delivered=delivered,
        scheduled_for=scheduled_for,
        delivered_at=delivered_at,
    )
    return _persist(session, event)


def list_notifications_for_user(
    session: Session,
    *,
    user_id: int,
    unread_only: bool,
    limit: int,
) -> list[NotificationEvent]:
    statement = (
        select(NotificationEvent)
        .where(NotificationEvent.user_id == user_id)
        .order_by(NotificationEvent.created_at.desc())
        .limit(limit)
    )
    if unread_only:
        statement = statement.where(NotificationEvent.is_read.is_(False))
    return list(session.exec(statement).all())


def get_notification_or_404(session: Session, *, notification_id: int) -> NotificationEvent:
    event = session.get(NotificationEvent, notification_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return event


def update_notification_event(
    session: Session,
    *,
    event: NotificationEvent,
    is_read: bool | None = None,
    delivered: bool | None = None,
) -> NotificationEvent:
    if is_read is not None:
        event.is_read = is_read
    if delivered is not None:
        event.delivered = delivered
        event.delivered_at = utc_now() if delivered else None
    event.updated_at = utc_now()
    return _persist(session, event)


def mark_all_notifications_read(session: Session, *, user_id: int) -> int:
    rows = list(session.exec(select(NotificationEvent).where(NotificationEvent.user_id == user_id, NotificationEvent.is_read.is_(False))).all())
    for row in rows:
        row.is_read = True
        row.updated_at = utc_now()
        session.add(row)
    session.commit()
    return len(rows)


def _localized_book_payload(session: Session, *, book: Book, language: str) -> dict[str, object]:
    normalized_language = normalize_language(language)
    translation = get_book_translation(session, book_id=book.id, language=normalized_language)
    return {
        "book_id": book.id,
        "title": translation.title if translation is not None else book.title,
        "cover_image_url": book.cover_image_url,
        "age_band": book.age_band,
        "content_lane_key": book.content_lane_key,
        "language": book.language,
        "published": book.published,
        "publication_status": book.publication_status,
    }


def _child_profile_for_request(session: Session, *, user: User, child_profile_id: int | None) -> ChildProfile | None:
    if child_profile_id is None:
        return None
    return get_child_profile_for_user(session, user_id=user.id, child_profile_id=child_profile_id)


def get_daily_story_suggestion(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
    suggestion_date: date,
) -> DailyStorySuggestion | None:
    statement = select(DailyStorySuggestion).where(
        DailyStorySuggestion.user_id == user_id,
        DailyStorySuggestion.suggestion_date == suggestion_date,
    )
    if child_profile_id is None:
        statement = statement.where(DailyStorySuggestion.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(DailyStorySuggestion.child_profile_id == child_profile_id)
    return session.exec(statement).first()


def _eligible_daily_story(
    session: Session,
    *,
    user: User,
    child_profile: ChildProfile | None,
    target_date: date,
) -> tuple[dict[str, object], str] | None:
    pack_candidate = get_existing_pack_story_candidate(
        session,
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        target_date=target_date,
    )
    if pack_candidate is not None:
        pack, pack_item = pack_candidate
        pack_book = session.get(Book, pack_item.book_id)
        if pack_book is not None:
            return (
                _localized_book_payload(
                    session,
                    book=pack_book,
                    language=child_profile.language if child_profile is not None else user.language,
                ),
                f"First pending story from tonight's bedtime pack: {pack.title}",
            )
    plan_candidate = get_plan_story_candidate(
        session,
        user=user,
        child_profile_id=child_profile.id if child_profile is not None else None,
        target_date=target_date,
    )
    if plan_candidate is not None:
        book, reason = plan_candidate
        return (
            _localized_book_payload(
                session,
                book=book,
                language=child_profile.language if child_profile is not None else user.language,
            ),
            reason,
        )
    items, _count = get_personalized_recommendations_for_user(
        session,
        user=user,
        child_profile_id=child_profile.id if child_profile is not None else None,
        age_band=child_profile.age_band if child_profile is not None else None,
        limit=8,
    )
    if not items:
        return None
    controls = resolve_parental_controls(session, user=user, child_profile_id=child_profile.id if child_profile is not None else None)
    preferred = sorted(
        items,
        key=lambda item: (
            0
            if controls.bedtime_mode_enabled and item.content_lane_key == "bedtime_3_7"
            else 1,
            -item.score,
        ),
    )[0]
    return preferred.model_dump(), preferred.reasons[0] if preferred.reasons else "Selected for today"


def _create_daily_story_notification_events(
    session: Session,
    *,
    user: User,
    child_profile: ChildProfile | None,
    book_payload: dict[str, object],
    reason: str,
) -> None:
    preference = get_or_create_notification_preference(session, user_id=user.id)
    child_name = child_profile.display_name if child_profile is not None else "your family"
    metadata = {"book_id": book_payload["book_id"], "reason": reason}
    if preference.enable_new_story_alerts and preference.enable_in_app:
        create_notification_event(
            session,
            user_id=user.id,
            child_profile_id=child_profile.id if child_profile is not None else None,
            notification_type="new_story_recommendation",
            delivery_channel="in_app",
            title="Today’s story is ready",
            body=f"A new bedtime pick is ready for {child_name}.",
            metadata=metadata,
            delivered=True,
            delivered_at=utc_now(),
        )
        track_event_safe(
            session,
            event_name="new_story_alert_created",
            user=user,
            child_profile_id=child_profile.id if child_profile is not None else None,
            book_id=int(book_payload["book_id"]),
            metadata={"channel": "in_app"},
        )
    if preference.enable_new_story_alerts and preference.enable_email_placeholder:
        create_notification_event(
            session,
            user_id=user.id,
            child_profile_id=child_profile.id if child_profile is not None else None,
            notification_type="new_story_recommendation",
            delivery_channel="email_placeholder",
            title="Today’s story email placeholder",
            body=f"Placeholder email for today’s story suggestion for {child_name}.",
            metadata=metadata,
            scheduled_for=utc_now(),
        )


def maybe_create_bedtime_reminder_for_user(
    session: Session,
    *,
    user: User,
    child_profile: ChildProfile | None,
    target_date: date,
) -> NotificationEvent | None:
    preference = get_or_create_notification_preference(session, user_id=user.id)
    controls = resolve_parental_controls(session, user=user, child_profile_id=child_profile.id if child_profile is not None else None)
    if not preference.enable_bedtime_reminders or not preference.enable_in_app or not controls.bedtime_mode_enabled:
        return None
    existing = [
        event
        for event in list_notifications_for_user(session, user_id=user.id, unread_only=False, limit=500)
        if event.notification_type == "bedtime_reminder"
        and event.child_profile_id == (child_profile.id if child_profile is not None else None)
        and event.created_at.date() == target_date
    ]
    if existing:
        return existing[0]
    reminder = create_notification_event(
        session,
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        notification_type="bedtime_reminder",
        delivery_channel="in_app",
        title="Bedtime story reminder",
        body=f"It’s a good time to open Buddybug for {child_profile.display_name if child_profile is not None else 'tonight’s story'}.",
        delivered=True,
        delivered_at=utc_now(),
        scheduled_for=datetime.combine(target_date, time(hour=19, minute=0)),
    )
    track_event_safe(
        session,
        event_name="bedtime_reminder_created",
        user=user,
        child_profile_id=child_profile.id if child_profile is not None else None,
        metadata={"scheduled_date": str(target_date)},
    )
    return reminder


def generate_daily_story_suggestion(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
    target_date: date | None = None,
) -> DailyStorySuggestionResponse:
    resolved_date = target_date or utc_now().date()
    child_profile = _child_profile_for_request(session, user=user, child_profile_id=child_profile_id)
    existing = get_daily_story_suggestion(
        session,
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        suggestion_date=resolved_date,
    )
    if existing is not None:
        book = session.get(Book, existing.book_id)
        book_payload = (
            _localized_book_payload(
                session,
                book=book,
                language=child_profile.language if child_profile is not None else user.language,
            )
            if book is not None
            else None
        )
        return DailyStorySuggestionResponse(suggestion=existing, book=book_payload)

    eligible = _eligible_daily_story(session, user=user, child_profile=child_profile, target_date=resolved_date)
    if eligible is None:
        maybe_create_bedtime_reminder_for_user(session, user=user, child_profile=child_profile, target_date=resolved_date)
        return DailyStorySuggestionResponse(suggestion=None, book=None)
    book_payload, reason = eligible
    suggestion = DailyStorySuggestion(
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        book_id=int(book_payload["book_id"]),
        suggestion_date=resolved_date,
        reason=reason,
    )
    suggestion = _persist(session, suggestion)
    _create_daily_story_notification_events(
        session,
        user=user,
        child_profile=child_profile,
        book_payload=book_payload,
        reason=reason,
    )
    maybe_create_bedtime_reminder_for_user(session, user=user, child_profile=child_profile, target_date=resolved_date)
    track_event_safe(
        session,
        event_name="daily_story_suggested",
        user=user,
        child_profile_id=child_profile.id if child_profile is not None else None,
        book_id=suggestion.book_id,
        metadata={"suggestion_date": str(resolved_date)},
    )
    return DailyStorySuggestionResponse(suggestion=suggestion, book=book_payload)
