from __future__ import annotations

import hashlib
import json
import logging
from datetime import timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import AnalyticsEvent, Book, ExperimentAssignment, User
from app.schemas.analytics_schema import AnalyticsSummaryResponse, ExperimentVariantResponse
from app.services.review_service import utc_now

logger = logging.getLogger(__name__)

ALLOWED_ANALYTICS_EVENTS = {
    "app_opened",
    "library_viewed",
    "book_opened",
    "book_page_viewed",
    "book_completed",
    "book_replayed",
    "audio_started",
    "audio_completed",
    "voice_selected",
    "bedtime_mode_used",
    "autoplay_blocked_by_parental_controls",
    "age_band_filtered_by_parental_controls",
    "daily_story_suggested",
    "notification_read",
    "bedtime_reminder_created",
    "new_story_alert_created",
    "discovery_search",
    "discovery_collection_opened",
    "discovery_book_opened",
    "featured_collection_viewed",
    "marketing_home_viewed",
    "marketing_pricing_viewed",
    "marketing_features_viewed",
    "marketing_cta_clicked",
    "marketing_faq_viewed",
    "support_ticket_created",
    "support_ticket_resolved",
    "support_ticket_closed",
    "support_ticket_note_added_internal",
    "recommendation_viewed",
    "recommendation_clicked",
    "preview_wall_hit",
    "feedback_submitted",
    "book_saved",
    "book_archived",
    "offline_marked",
    "download_started",
    "download_completed",
    "checkout_started",
    "checkout_completed",
    "billing_portal_opened",
    "billing_recovery_prompt_viewed",
    "billing_recovery_prompt_clicked",
    "billing_recovery_case_opened",
    "billing_recovery_case_resolved",
    "language_changed",
    "feature_flag_admin_updated",
    "achievement_earned",
    "achievement_dashboard_viewed",
    "streak_updated",
    "privacy_preferences_updated",
    "data_export_requested",
    "data_deletion_requested",
    "referral_code_viewed",
    "referral_signup_attributed",
    "referral_premium_converted",
    "gift_subscription_created",
    "gift_subscription_redeemed",
    "pwa_installed",
    "offline_book_saved",
    "offline_reader_opened",
    "offline_sync_flushed",
    "settings_opened",
    "downloads_settings_opened",
    "about_opened",
    "app_shell_navigation_used",
    "onboarding_started",
    "onboarding_step_completed",
    "onboarding_skipped",
    "onboarding_completed",
    "onboarding_first_story_opened",
    "reengagement_suggestion_viewed",
    "reengagement_suggestion_dismissed",
    "reengagement_dashboard_opened",
    "read_along_session_created",
    "read_along_session_joined",
    "read_along_page_synced",
    "read_along_session_ended",
    "family_digest_generated",
    "family_digest_viewed",
    "family_digest_summary_card_viewed",
    "reading_plan_created",
    "reading_plan_updated",
    "reading_plan_session_completed",
    "reading_plan_suggestions_viewed",
    "child_comfort_profile_updated",
    "story_quality_review_completed",
    "illustration_quality_review_completed",
    "story_flagged_for_review",
    "bedtime_pack_generated",
    "bedtime_pack_viewed",
    "bedtime_pack_item_opened",
    "bedtime_pack_item_completed",
    "bedtime_pack_completed",
    "message_variant_exposed",
    "message_variant_clicked",
    "preview_wall_upgrade_clicked",
    "pricing_cta_clicked",
    "promo_code_redeemed",
    "promo_code_failed",
    "beta_cohort_membership_added",
    "beta_cohort_membership_removed",
    "beta_access_checked",
}

FUNNEL_EVENT_NAMES = [
    "library_viewed",
    "book_opened",
    "preview_wall_hit",
    "checkout_started",
    "checkout_completed",
]


def _validate_event_name(event_name: str) -> str:
    if event_name not in ALLOWED_ANALYTICS_EVENTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid analytics event_name")
    return event_name


def _serialize_metadata(metadata: dict[str, Any] | None = None, metadata_json: str | None = None) -> str | None:
    if metadata_json is not None:
        try:
            parsed = json.loads(metadata_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid metadata_json: {exc.msg}")
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="metadata_json must decode to an object")
        return json.dumps(parsed, default=str, sort_keys=True)
    if metadata is None:
        return None
    return json.dumps(metadata, default=str, sort_keys=True)


def build_event(
    *,
    event_name: str,
    user: User | None = None,
    user_id: int | None = None,
    child_profile_id: int | None = None,
    reader_identifier: str | None = None,
    book_id: int | None = None,
    session_id: str | None = None,
    language: str | None = None,
    country: str | None = None,
    experiment_key: str | None = None,
    experiment_variant: str | None = None,
    metadata: dict[str, Any] | None = None,
    metadata_json: str | None = None,
) -> AnalyticsEvent:
    resolved_user_id = user.id if user is not None else user_id
    resolved_language = language or (user.language if user is not None else None)
    resolved_country = country or (user.country if user is not None else None)
    return AnalyticsEvent(
        event_name=_validate_event_name(event_name),
        user_id=resolved_user_id,
        child_profile_id=child_profile_id,
        reader_identifier=reader_identifier,
        book_id=book_id,
        session_id=session_id,
        language=resolved_language,
        country=resolved_country,
        experiment_key=experiment_key,
        experiment_variant=experiment_variant,
        metadata_json=_serialize_metadata(metadata=metadata, metadata_json=metadata_json),
        occurred_at=utc_now(),
    )


def track_event(
    session: Session,
    *,
    event_name: str,
    user: User | None = None,
    user_id: int | None = None,
    child_profile_id: int | None = None,
    reader_identifier: str | None = None,
    book_id: int | None = None,
    session_id: str | None = None,
    language: str | None = None,
    country: str | None = None,
    experiment_key: str | None = None,
    experiment_variant: str | None = None,
    metadata: dict[str, Any] | None = None,
    metadata_json: str | None = None,
) -> AnalyticsEvent:
    event = build_event(
        event_name=event_name,
        user=user,
        user_id=user_id,
        child_profile_id=child_profile_id,
        reader_identifier=reader_identifier,
        book_id=book_id,
        session_id=session_id,
        language=language,
        country=country,
        experiment_key=experiment_key,
        experiment_variant=experiment_variant,
        metadata=metadata,
        metadata_json=metadata_json,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def track_event_safe(session: Session, **kwargs: Any) -> AnalyticsEvent | None:
    try:
        return track_event(session, **kwargs)
    except Exception:
        session.rollback()
        logger.warning("Failed to persist analytics event", exc_info=True, extra={"event_name": kwargs.get("event_name")})
        return None


def list_analytics_events(
    session: Session,
    *,
    event_name: str | None,
    user_id: int | None,
    book_id: int | None,
    language: str | None,
    limit: int,
) -> list[AnalyticsEvent]:
    statement = select(AnalyticsEvent).order_by(AnalyticsEvent.occurred_at.desc()).limit(limit)
    if event_name is not None:
        _validate_event_name(event_name)
        statement = statement.where(AnalyticsEvent.event_name == event_name)
    if user_id is not None:
        statement = statement.where(AnalyticsEvent.user_id == user_id)
    if book_id is not None:
        statement = statement.where(AnalyticsEvent.book_id == book_id)
    if language is not None:
        statement = statement.where(AnalyticsEvent.language == language)
    return list(session.exec(statement).all())


def _events_since(session: Session, *, days: int) -> list[AnalyticsEvent]:
    since = utc_now() - timedelta(days=days)
    statement = (
        select(AnalyticsEvent)
        .where(AnalyticsEvent.occurred_at >= since)
        .order_by(AnalyticsEvent.occurred_at.desc())
    )
    return list(session.exec(statement).all())


def get_event_counts(session: Session, *, days: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in _events_since(session, days=days):
        counts[event.event_name] = counts.get(event.event_name, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def get_top_books(session: Session, *, days: int, limit: int = 5) -> list[dict[str, Any]]:
    events = [event for event in _events_since(session, days=days) if event.book_id is not None]
    aggregates: dict[int, dict[str, int]] = {}
    for event in events:
        book_stats = aggregates.setdefault(
            event.book_id,
            {"opens": 0, "completions": 0, "replays": 0, "audio_starts": 0, "recommendation_clicks": 0},
        )
        if event.event_name == "book_opened":
            book_stats["opens"] += 1
        elif event.event_name == "book_completed":
            book_stats["completions"] += 1
        elif event.event_name == "book_replayed":
            book_stats["replays"] += 1
        elif event.event_name == "audio_started":
            book_stats["audio_starts"] += 1
        elif event.event_name == "recommendation_clicked":
            book_stats["recommendation_clicks"] += 1

    results: list[dict[str, Any]] = []
    for book_id, stats in aggregates.items():
        book = session.get(Book, book_id)
        results.append(
            {
                "book_id": book_id,
                "title": book.title if book is not None else f"Book {book_id}",
                **stats,
                "total": sum(stats.values()),
            }
        )
    results.sort(key=lambda item: (-item["total"], -item["opens"], item["book_id"]))
    return results[:limit]


def get_funnel_counts(session: Session, *, days: int) -> dict[str, int]:
    counts = {name: 0 for name in FUNNEL_EVENT_NAMES}
    for event in _events_since(session, days=days):
        if event.event_name in counts:
            counts[event.event_name] += 1
    return counts


def get_admin_summary(session: Session, *, days: int) -> AnalyticsSummaryResponse:
    events = _events_since(session, days=days)
    unique_users = {event.user_id for event in events if event.user_id is not None}
    unique_readers = {event.reader_identifier for event in events if event.reader_identifier}
    return AnalyticsSummaryResponse(
        total_events=len(events),
        unique_users=len(unique_users),
        unique_readers=len(unique_readers),
        top_books=get_top_books(session, days=days),
        top_event_counts=get_event_counts(session, days=days),
    )


def get_existing_assignment(
    session: Session,
    *,
    experiment_key: str,
    user_id: int | None,
    reader_identifier: str | None,
) -> ExperimentAssignment | None:
    if user_id is not None:
        statement = select(ExperimentAssignment).where(
            ExperimentAssignment.experiment_key == experiment_key,
            ExperimentAssignment.user_id == user_id,
        )
        assignment = session.exec(statement).first()
        if assignment is not None:
            return assignment
    if reader_identifier:
        statement = select(ExperimentAssignment).where(
            ExperimentAssignment.experiment_key == experiment_key,
            ExperimentAssignment.reader_identifier == reader_identifier,
        )
        return session.exec(statement).first()
    return None


def deterministic_variant_for_reader(experiment_key: str, identity: str, variants: list[str]) -> str:
    if not variants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment variants are required")
    digest = hashlib.sha256(f"{experiment_key}:{identity}".encode("utf-8")).hexdigest()
    index = int(digest[:12], 16) % len(variants)
    return variants[index]


def assign_experiment_variant(
    session: Session,
    *,
    experiment_key: str,
    variants: list[str],
    user: User | None = None,
    reader_identifier: str | None = None,
    sticky: bool = True,
) -> ExperimentVariantResponse:
    identity = f"user:{user.id}" if user is not None else (reader_identifier.strip() if reader_identifier else "")
    if not identity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="reader_identifier is required for anonymous experiment assignment")

    existing = get_existing_assignment(
        session,
        experiment_key=experiment_key,
        user_id=user.id if user is not None else None,
        reader_identifier=reader_identifier,
    )
    if existing is not None:
        return ExperimentVariantResponse(experiment_key=experiment_key, variant=existing.variant, assigned=True)

    variant = deterministic_variant_for_reader(experiment_key, identity, variants)
    if not sticky:
        return ExperimentVariantResponse(experiment_key=experiment_key, variant=variant, assigned=False)

    assignment = ExperimentAssignment(
        experiment_key=experiment_key,
        user_id=user.id if user is not None else None,
        reader_identifier=None if user is not None else reader_identifier,
        variant=variant,
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return ExperimentVariantResponse(experiment_key=experiment_key, variant=assignment.variant, assigned=True)
