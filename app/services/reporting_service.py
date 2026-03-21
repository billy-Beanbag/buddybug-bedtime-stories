from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    AnalyticsEvent,
    Book,
    ChildProfile,
    DailyStorySuggestion,
    ReadingProgress,
    SupportTicket,
    User,
    UserLibraryItem,
    UserStoryFeedback,
)
from app.schemas.reporting_schema import (
    ContentPerformanceItem,
    ContentPerformanceResponse,
    EngagementMetricsResponse,
    KPIOverviewResponse,
    SegmentBreakdownItem,
    SegmentBreakdownResponse,
    SubscriptionMetricsResponse,
    SupportMetricsResponse,
)
from app.services.review_service import utc_now


@dataclass
class ReportingWindow:
    start_at: datetime
    end_at: datetime


def _percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def parse_reporting_window(
    *,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
) -> ReportingWindow:
    now = utc_now()
    if start_date is not None or end_date is not None:
        if start_date is None or end_date is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date and end_date must be supplied together")
        if start_date > end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")
        start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        end_at = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        return ReportingWindow(start_at=start_at, end_at=end_at)
    resolved_days = days or 30
    if resolved_days <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="days must be greater than 0")
    return ReportingWindow(start_at=now - timedelta(days=resolved_days), end_at=now)


def _events_in_window(session: Session, *, window: ReportingWindow) -> list[AnalyticsEvent]:
    statement = (
        select(AnalyticsEvent)
        .where(AnalyticsEvent.occurred_at >= window.start_at, AnalyticsEvent.occurred_at <= window.end_at)
        .order_by(AnalyticsEvent.occurred_at.desc())
    )
    return list(session.exec(statement).all())


def _published_books(session: Session) -> list[Book]:
    return list(session.exec(select(Book).where(Book.published.is_(True), Book.publication_status == "published")).all())


def _parse_reader_identifier_user_id(reader_identifier: str | None) -> int | None:
    if not reader_identifier or not reader_identifier.startswith("user:"):
        return None
    try:
        return int(reader_identifier.split(":", 1)[1])
    except (TypeError, ValueError):
        return None


def _active_user_ids(session: Session, *, window: ReportingWindow, events: list[AnalyticsEvent]) -> set[int]:
    active_user_ids = {event.user_id for event in events if event.user_id is not None}
    active_user_ids.update(
        user_id
        for user_id in (_parse_reader_identifier_user_id(progress.reader_identifier) for progress in session.exec(
            select(ReadingProgress).where(
                ReadingProgress.last_opened_at >= window.start_at,
                ReadingProgress.last_opened_at <= window.end_at,
            )
        ).all())
        if user_id is not None
    )
    active_user_ids.update(
        row.user_id
        for row in session.exec(
            select(UserStoryFeedback).where(
                UserStoryFeedback.updated_at >= window.start_at,
                UserStoryFeedback.updated_at <= window.end_at,
            )
        ).all()
    )
    active_user_ids.update(
        row.user_id
        for row in session.exec(
            select(UserLibraryItem).where(
                UserLibraryItem.updated_at >= window.start_at,
                UserLibraryItem.updated_at <= window.end_at,
            )
        ).all()
    )
    return {user_id for user_id in active_user_ids if user_id is not None}


def _active_child_profile_ids(session: Session, *, window: ReportingWindow, events: list[AnalyticsEvent]) -> set[int]:
    active_child_profile_ids = {event.child_profile_id for event in events if event.child_profile_id is not None}
    active_child_profile_ids.update(
        row.child_profile_id
        for row in session.exec(
            select(ReadingProgress).where(
                ReadingProgress.child_profile_id != None,  # noqa: E711
                ReadingProgress.last_opened_at >= window.start_at,
                ReadingProgress.last_opened_at <= window.end_at,
            )
        ).all()
        if row.child_profile_id is not None
    )
    active_child_profile_ids.update(
        row.child_profile_id
        for row in session.exec(
            select(UserStoryFeedback).where(
                UserStoryFeedback.child_profile_id != None,  # noqa: E711
                UserStoryFeedback.updated_at >= window.start_at,
                UserStoryFeedback.updated_at <= window.end_at,
            )
        ).all()
        if row.child_profile_id is not None
    )
    active_child_profile_ids.update(
        row.child_profile_id
        for row in session.exec(
            select(UserLibraryItem).where(
                UserLibraryItem.child_profile_id != None,  # noqa: E711
                UserLibraryItem.updated_at >= window.start_at,
                UserLibraryItem.updated_at <= window.end_at,
            )
        ).all()
        if row.child_profile_id is not None
    )
    active_child_profile_ids.update(
        row.child_profile_id
        for row in session.exec(
            select(DailyStorySuggestion).where(
                DailyStorySuggestion.child_profile_id != None,  # noqa: E711
                DailyStorySuggestion.created_at >= window.start_at,
                DailyStorySuggestion.created_at <= window.end_at,
            )
        ).all()
        if row.child_profile_id is not None
    )
    return {child_profile_id for child_profile_id in active_child_profile_ids if child_profile_id is not None}


def _total_downloads(session: Session) -> int:
    analytics_downloads = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.event_name == "download_completed")
    ).all()
    if analytics_downloads:
        return len(analytics_downloads)
    return len(
        session.exec(select(UserLibraryItem).where(UserLibraryItem.downloaded_at != None)).all()  # noqa: E711
    )


def get_kpi_overview(
    session: Session,
    *,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
) -> KPIOverviewResponse:
    window = parse_reporting_window(days=days, start_date=start_date, end_date=end_date)
    events = _events_in_window(session, window=window)
    users = list(session.exec(select(User)).all())
    child_profiles = list(session.exec(select(ChildProfile)).all())
    published_books = _published_books(session)
    premium_users = [user for user in users if user.subscription_tier == "premium"]
    open_support_tickets = session.exec(select(SupportTicket).where(SupportTicket.status == "open")).all()
    saved_library_items = session.exec(select(UserLibraryItem).where(UserLibraryItem.status == "saved")).all()
    return KPIOverviewResponse(
        total_users=len(users),
        active_users_30d=len(_active_user_ids(session, window=window, events=events)),
        total_child_profiles=len(child_profiles),
        active_child_profiles_30d=len(_active_child_profile_ids(session, window=window, events=events)),
        total_premium_users=len(premium_users),
        premium_conversion_rate=_percent(len(premium_users), len(users)),
        total_published_books=len(published_books),
        total_saved_library_items=len(saved_library_items),
        total_downloads=_total_downloads(session),
        total_support_tickets_open=len(open_support_tickets),
        generated_at=utc_now(),
    )


def get_engagement_metrics(
    session: Session,
    *,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
) -> EngagementMetricsResponse:
    window = parse_reporting_window(days=days, start_date=start_date, end_date=end_date)
    events = _events_in_window(session, window=window)
    event_counts = Counter(event.event_name for event in events)
    daily_story_views = event_counts.get("daily_story_suggested", 0)
    if daily_story_views == 0:
        daily_story_views = len(
            session.exec(
                select(DailyStorySuggestion).where(
                    DailyStorySuggestion.created_at >= window.start_at,
                    DailyStorySuggestion.created_at <= window.end_at,
                )
            ).all()
        )
    opens = event_counts.get("book_opened", 0)
    completions = event_counts.get("book_completed", 0)
    return EngagementMetricsResponse(
        book_opens_30d=opens,
        book_completions_30d=completions,
        book_replays_30d=event_counts.get("book_replayed", 0),
        narration_starts_30d=event_counts.get("audio_started", 0),
        narration_completions_30d=event_counts.get("audio_completed", 0),
        daily_story_views_30d=daily_story_views,
        avg_completion_rate_30d=_percent(completions, opens),
    )


def get_subscription_metrics(
    session: Session,
    *,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
) -> SubscriptionMetricsResponse:
    window = parse_reporting_window(days=days, start_date=start_date, end_date=end_date)
    users = list(session.exec(select(User)).all())
    events = _events_in_window(session, window=window)
    free_users = [user for user in users if user.subscription_tier == "free"]
    premium_users = [user for user in users if user.subscription_tier == "premium"]
    trialing_users = [user for user in users if user.subscription_status == "trialing"]
    canceled_users = [user for user in users if user.subscription_status == "canceled"]
    event_counts = Counter(event.event_name for event in events)
    return SubscriptionMetricsResponse(
        free_users=len(free_users),
        premium_users=len(premium_users),
        trialing_users=len(trialing_users),
        canceled_users=len(canceled_users),
        active_conversion_rate=_percent(len(premium_users), len(users)),
        checkout_started_30d=event_counts.get("checkout_started", 0),
        checkout_completed_30d=event_counts.get("checkout_completed", 0),
    )


def get_top_content_performance(
    session: Session,
    *,
    limit: int,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
) -> ContentPerformanceResponse:
    window = parse_reporting_window(days=days, start_date=start_date, end_date=end_date)
    published_books_by_id = {book.id: book for book in _published_books(session)}
    events = [
        event
        for event in _events_in_window(session, window=window)
        if event.book_id is not None and event.book_id in published_books_by_id
    ]
    aggregates: dict[int, dict[str, int]] = {}
    for event in events:
        book_stats = aggregates.setdefault(
            event.book_id,
            {"opens": 0, "completions": 0, "replays": 0, "downloads": 0, "narration_starts": 0},
        )
        if event.event_name == "book_opened":
            book_stats["opens"] += 1
        elif event.event_name == "book_completed":
            book_stats["completions"] += 1
        elif event.event_name == "book_replayed":
            book_stats["replays"] += 1
        elif event.event_name == "download_completed":
            book_stats["downloads"] += 1
        elif event.event_name == "audio_started":
            book_stats["narration_starts"] += 1
    if not any(stats["downloads"] for stats in aggregates.values()):
        for item in session.exec(
            select(UserLibraryItem).where(
                UserLibraryItem.book_id.in_(list(published_books_by_id.keys())),
                UserLibraryItem.downloaded_at != None,  # noqa: E711
                UserLibraryItem.downloaded_at >= window.start_at,
                UserLibraryItem.downloaded_at <= window.end_at,
            )
        ).all():
            aggregates.setdefault(
                item.book_id,
                {"opens": 0, "completions": 0, "replays": 0, "downloads": 0, "narration_starts": 0},
            )["downloads"] += 1
    items: list[ContentPerformanceItem] = []
    for book_id, stats in aggregates.items():
        book = published_books_by_id[book_id]
        items.append(
            ContentPerformanceItem(
                book_id=book.id,
                title=book.title,
                language=book.language,
                age_band=book.age_band,
                content_lane_key=book.content_lane_key,
                opens=stats["opens"],
                completions=stats["completions"],
                replays=stats["replays"],
                downloads=stats["downloads"],
                narration_starts=stats["narration_starts"],
            )
        )
    items.sort(
        key=lambda item: (
            item.opens + item.completions + item.replays + item.downloads + item.narration_starts,
            item.opens,
            item.book_id,
        ),
        reverse=True,
    )
    return ContentPerformanceResponse(items=items[:limit])


def _breakdown_from_content_items(items: list[ContentPerformanceItem], *, attribute: str) -> SegmentBreakdownResponse:
    counts: Counter[str] = Counter()
    for item in items:
        value = getattr(item, attribute) or "unknown"
        total_activity = item.opens + item.completions + item.replays + item.downloads + item.narration_starts
        counts[str(value)] += max(total_activity, 1)
    ordered = sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))
    return SegmentBreakdownResponse(items=[SegmentBreakdownItem(key=key, count=count) for key, count in ordered])


def _published_book_segment_breakdown(session: Session, *, attribute: str) -> SegmentBreakdownResponse:
    counts: Counter[str] = Counter()
    for book in _published_books(session):
        value = getattr(book, attribute) or "unknown"
        counts[str(value)] += 1
    ordered = sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))
    return SegmentBreakdownResponse(items=[SegmentBreakdownItem(key=key, count=count) for key, count in ordered])


def get_language_breakdown(
    session: Session,
    *,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
) -> SegmentBreakdownResponse:
    items = get_top_content_performance(session, limit=500, days=days, start_date=start_date, end_date=end_date).items
    return _breakdown_from_content_items(items, attribute="language") if items else _published_book_segment_breakdown(session, attribute="language")


def get_age_band_breakdown(
    session: Session,
    *,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
) -> SegmentBreakdownResponse:
    items = get_top_content_performance(session, limit=500, days=days, start_date=start_date, end_date=end_date).items
    return _breakdown_from_content_items(items, attribute="age_band") if items else _published_book_segment_breakdown(session, attribute="age_band")


def get_content_lane_breakdown(
    session: Session,
    *,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
) -> SegmentBreakdownResponse:
    items = get_top_content_performance(session, limit=500, days=days, start_date=start_date, end_date=end_date).items
    if items:
        counts: Counter[str] = Counter()
        for item in items:
            total_activity = item.opens + item.completions + item.replays + item.downloads + item.narration_starts
            counts[item.content_lane_key or "unknown"] += max(total_activity, 1)
        ordered = sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))
        return SegmentBreakdownResponse(items=[SegmentBreakdownItem(key=key, count=count) for key, count in ordered])
    return _published_book_segment_breakdown(session, attribute="content_lane_key")


def get_support_metrics(
    session: Session,
    *,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
) -> SupportMetricsResponse:
    window = parse_reporting_window(days=days, start_date=start_date, end_date=end_date)
    open_tickets = session.exec(select(SupportTicket).where(SupportTicket.status == "open")).all()
    in_progress_tickets = session.exec(select(SupportTicket).where(SupportTicket.status == "in_progress")).all()
    resolved_tickets = session.exec(
        select(SupportTicket).where(
            SupportTicket.resolved_at != None,  # noqa: E711
            SupportTicket.resolved_at >= window.start_at,
            SupportTicket.resolved_at <= window.end_at,
        )
    ).all()
    if resolved_tickets:
        avg_resolution_hours = round(
            sum((ticket.resolved_at - ticket.created_at).total_seconds() / 3600 for ticket in resolved_tickets if ticket.resolved_at is not None)
            / len(resolved_tickets),
            2,
        )
    else:
        avg_resolution_hours = None
    return SupportMetricsResponse(
        open_tickets=len(open_tickets),
        in_progress_tickets=len(in_progress_tickets),
        resolved_30d=len(resolved_tickets),
        avg_resolution_hours=avg_resolution_hours,
    )
