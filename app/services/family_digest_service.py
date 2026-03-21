from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    AnalyticsEvent,
    Book,
    ChildProfile,
    EarnedAchievement,
    FamilyDigest,
    FamilyDigestChildSummary,
    ReadingPlan,
    ReadingPlanSession,
    ReadingStreakSnapshot,
    User,
    UserLibraryItem,
)
from app.schemas.family_digest_schema import FamilyDigestSummaryCardResponse
from app.services.review_service import utc_now

FAMILY_DIGEST_TYPE_WEEKLY = "weekly_family_summary"


def get_week_window(reference_date: date | None = None) -> tuple[date, date]:
    effective_today = reference_date or utc_now().date()
    period_end = effective_today - timedelta(days=1)
    period_start = period_end - timedelta(days=6)
    return period_start, period_end


def _window_bounds(period_start: date, period_end: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(period_start, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(period_end + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return start_dt, end_dt


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_summary(summary: dict[str, object]) -> str:
    return json.dumps(summary, default=str, sort_keys=True)


def _parse_summary_json(summary_json: str) -> dict[str, object]:
    try:
        parsed = json.loads(summary_json)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _get_digest_for_period(
    session: Session,
    *,
    user_id: int,
    digest_type: str,
    period_start: date,
    period_end: date,
) -> FamilyDigest | None:
    statement = select(FamilyDigest).where(
        FamilyDigest.user_id == user_id,
        FamilyDigest.digest_type == digest_type,
        FamilyDigest.period_start == period_start,
        FamilyDigest.period_end == period_end,
    )
    return session.exec(statement).first()


def _list_child_summaries(session: Session, *, family_digest_id: int) -> list[FamilyDigestChildSummary]:
    statement = (
        select(FamilyDigestChildSummary)
        .where(FamilyDigestChildSummary.family_digest_id == family_digest_id)
        .order_by(FamilyDigestChildSummary.child_profile_id.asc())
    )
    return list(session.exec(statement).all())


def _list_active_child_profiles(session: Session, *, user_id: int) -> list[ChildProfile]:
    statement = (
        select(ChildProfile)
        .where(ChildProfile.user_id == user_id, ChildProfile.is_active.is_(True))
        .order_by(ChildProfile.created_at.asc())
    )
    return list(session.exec(statement).all())


def _events_for_user_in_period(
    session: Session,
    *,
    user_id: int,
    period_start: date,
    period_end: date,
) -> list[AnalyticsEvent]:
    start_dt, end_dt = _window_bounds(period_start, period_end)
    statement = select(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id)
    events = list(session.exec(statement).all())
    return [
        event
        for event in events
        if start_dt <= _normalize_datetime(event.occurred_at) < end_dt
    ]


def _earned_achievements_for_user_in_period(
    session: Session,
    *,
    user_id: int,
    period_start: date,
    period_end: date,
) -> list[EarnedAchievement]:
    start_dt, end_dt = _window_bounds(period_start, period_end)
    statement = select(EarnedAchievement).where(EarnedAchievement.user_id == user_id)
    items = list(session.exec(statement).all())
    return [
        item
        for item in items
        if start_dt <= _normalize_datetime(item.earned_at) < end_dt
    ]


def _saved_library_items_for_user_in_period(
    session: Session,
    *,
    user_id: int,
    period_start: date,
    period_end: date,
) -> list[UserLibraryItem]:
    start_dt, end_dt = _window_bounds(period_start, period_end)
    statement = select(UserLibraryItem).where(
        UserLibraryItem.user_id == user_id,
        UserLibraryItem.status == "saved",
    )
    items = list(session.exec(statement).all())
    return [
        item
        for item in items
        if start_dt <= _normalize_datetime(item.created_at) < end_dt
    ]


def _book_titles_for_ids(session: Session, *, book_ids: list[int]) -> list[str]:
    unique_ids = [book_id for index, book_id in enumerate(book_ids) if book_id not in book_ids[:index]]
    titles: list[str] = []
    for book_id in unique_ids:
        book = session.get(Book, book_id)
        if book is not None:
            titles.append(book.title)
    return titles


def _get_streak_days_in_period(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
    period_start: date,
) -> int:
    statement = select(ReadingStreakSnapshot).where(ReadingStreakSnapshot.user_id == user_id)
    if child_profile_id is None:
        statement = statement.where(ReadingStreakSnapshot.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(ReadingStreakSnapshot.child_profile_id == child_profile_id)
    snapshot = session.exec(statement).first()
    if snapshot is None or snapshot.last_read_date is None or snapshot.last_read_date < period_start:
        return 0
    return snapshot.current_streak_days


def _build_child_summary_text(
    *,
    child_name: str,
    stories_completed: int,
    narration_uses: int,
    achievements_earned: int,
    current_streak_days: int,
) -> str:
    if stories_completed and current_streak_days >= 3:
        return f"{child_name} kept a cozy reading rhythm going with {stories_completed} finished stor{'y' if stories_completed == 1 else 'ies'} this week."
    if stories_completed:
        return f"{child_name} finished {stories_completed} stor{'y' if stories_completed == 1 else 'ies'} this week."
    if narration_uses:
        return f"{child_name} spent time listening to narrated stories this week."
    if achievements_earned:
        return f"{child_name} earned a gentle Buddybug milestone this week."
    return f"{child_name} checked in for a calm Buddybug moment this week."


def build_child_digest_summary(
    session: Session,
    *,
    family_digest_id: int,
    user_id: int,
    child_profile: ChildProfile,
    period_start: date,
    events: list[AnalyticsEvent],
    earned_achievements: list[EarnedAchievement],
) -> FamilyDigestChildSummary | None:
    child_events = [event for event in events if event.child_profile_id == child_profile.id]
    child_achievements = [item for item in earned_achievements if item.child_profile_id == child_profile.id]
    stories_opened = sum(1 for event in child_events if event.event_name == "book_opened")
    stories_completed = sum(1 for event in child_events if event.event_name == "book_completed")
    narration_uses = sum(1 for event in child_events if event.event_name == "audio_started")
    achievements_earned = len(child_achievements)
    current_streak_days = _get_streak_days_in_period(
        session,
        user_id=user_id,
        child_profile_id=child_profile.id,
        period_start=period_start,
    )

    if not any([stories_opened, stories_completed, narration_uses, achievements_earned, current_streak_days]):
        return None

    return FamilyDigestChildSummary(
        family_digest_id=family_digest_id,
        child_profile_id=child_profile.id,
        stories_opened=stories_opened,
        stories_completed=stories_completed,
        narration_uses=narration_uses,
        achievements_earned=achievements_earned,
        current_streak_days=current_streak_days,
        summary_text=_build_child_summary_text(
            child_name=child_profile.display_name,
            stories_completed=stories_completed,
            narration_uses=narration_uses,
            achievements_earned=achievements_earned,
            current_streak_days=current_streak_days,
        ),
    )


def _choose_try_next_text(
    *,
    stories_completed: int,
    narration_uses: int,
    achievements_earned: int,
    saved_books_added: int,
    current_streak_days: int,
    active_plan_count: int,
) -> str:
    if active_plan_count > 0 and stories_completed == 0:
        return "One of your reading plans is ready for a gentle restart next week."
    if saved_books_added > 0:
        return "Try reopening one of the saved stories for an easy start to next week."
    if narration_uses == 0:
        return "A narrated story could be a lovely low-effort bedtime option next week."
    if current_streak_days >= 3:
        return "Keep the reading rhythm going with one short story at the usual cozy time."
    if achievements_earned > 0:
        return "Revisit a favorite story and build on this week’s gentle progress."
    if stories_completed == 0:
        return "One calm story together is a great way to restart the routine next week."
    return "Keep story time simple and steady with another familiar favorite next week."


def _build_highlight_text(
    *,
    stories_completed: int,
    achievements_earned: int,
    child_summary_count: int,
    narration_uses: int,
    most_active_child_name: str | None,
    completed_plan_sessions: int,
) -> str:
    if stories_completed == 0 and achievements_earned == 0 and narration_uses == 0:
        return "It was a quieter Buddybug week, which is okay. A single shared story can be a gentle restart."
    if completed_plan_sessions > 0:
        return (
            f"Your family completed {completed_plan_sessions} planned reading session{'s' if completed_plan_sessions != 1 else ''} "
            f"alongside {stories_completed} finished stor{'y' if stories_completed == 1 else 'ies'} this week."
        )
    if most_active_child_name and child_summary_count > 0:
        return (
            f"This week brought {stories_completed} completed stor{'y' if stories_completed == 1 else 'ies'}, "
            f"{achievements_earned} milestone{'s' if achievements_earned != 1 else ''}, and some lovely reading time for {most_active_child_name}."
        )
    return (
        f"This week brought {stories_completed} completed stor{'y' if stories_completed == 1 else 'ies'} "
        f"and {achievements_earned} gentle milestone{'s' if achievements_earned != 1 else ''} for your family."
    )


def build_family_digest_payload(
    session: Session,
    *,
    user: User,
    period_start: date,
    period_end: date,
) -> tuple[str, dict[str, object], list[FamilyDigestChildSummary]]:
    events = _events_for_user_in_period(session, user_id=user.id, period_start=period_start, period_end=period_end)
    earned_achievements = _earned_achievements_for_user_in_period(
        session,
        user_id=user.id,
        period_start=period_start,
        period_end=period_end,
    )
    saved_items = _saved_library_items_for_user_in_period(
        session,
        user_id=user.id,
        period_start=period_start,
        period_end=period_end,
    )
    active_plan_count = len(
        list(
            session.exec(
                select(ReadingPlan).where(ReadingPlan.user_id == user.id, ReadingPlan.status == "active")
            ).all()
        )
    )
    completed_plan_sessions = len(
        [
            item
            for item in session.exec(
                select(ReadingPlanSession, ReadingPlan)
                .join(ReadingPlan, ReadingPlan.id == ReadingPlanSession.reading_plan_id)
                .where(
                    ReadingPlan.user_id == user.id,
                    ReadingPlanSession.completed.is_(True),
                )
            ).all()
            if period_start <= item[0].scheduled_date <= period_end
        ]
    )

    child_profiles = _list_active_child_profiles(session, user_id=user.id)
    placeholder_digest_id = 0
    child_summaries = [
        child_summary
        for child_summary in (
            build_child_digest_summary(
                session,
                family_digest_id=placeholder_digest_id,
                user_id=user.id,
                child_profile=child_profile,
                period_start=period_start,
                events=events,
                earned_achievements=earned_achievements,
            )
            for child_profile in child_profiles
        )
        if child_summary is not None
    ]

    stories_opened = sum(1 for event in events if event.event_name == "book_opened")
    stories_completed = sum(1 for event in events if event.event_name == "book_completed")
    narration_uses = sum(1 for event in events if event.event_name == "audio_started")
    achievements_earned_count = len(earned_achievements)
    saved_books_added = len(saved_items)
    account_streak = _get_streak_days_in_period(
        session,
        user_id=user.id,
        child_profile_id=None,
        period_start=period_start,
    )

    most_active_child = None
    if child_summaries:
        most_active_child = max(
            child_summaries,
            key=lambda item: (
                item.stories_completed * 3
                + item.stories_opened * 2
                + item.narration_uses
                + item.achievements_earned * 2
                + item.current_streak_days
            ),
        )
    most_active_child_profile = (
        session.get(ChildProfile, most_active_child.child_profile_id) if most_active_child is not None else None
    )

    completed_book_ids = [event.book_id for event in events if event.event_name == "book_completed" and event.book_id is not None]
    completed_story_titles = _book_titles_for_ids(session, book_ids=completed_book_ids)[:3]

    summary_payload: dict[str, object] = {
        "highlight_text": _build_highlight_text(
            stories_completed=stories_completed,
            achievements_earned=achievements_earned_count,
            child_summary_count=len(child_summaries),
            narration_uses=narration_uses,
            most_active_child_name=most_active_child_profile.display_name if most_active_child_profile is not None else None,
            completed_plan_sessions=completed_plan_sessions,
        ),
        "try_next_text": _choose_try_next_text(
            stories_completed=stories_completed,
            narration_uses=narration_uses,
            achievements_earned=achievements_earned_count,
            saved_books_added=saved_books_added,
            current_streak_days=account_streak,
            active_plan_count=active_plan_count,
        ),
        "stories_opened": stories_opened,
        "stories_completed": stories_completed,
        "achievements_earned": achievements_earned_count,
        "narration_uses": narration_uses,
        "saved_books_added": saved_books_added,
        "active_child_profiles": len(child_summaries),
        "most_active_child_profile_id": most_active_child.child_profile_id if most_active_child is not None else None,
        "most_active_child_name": most_active_child_profile.display_name if most_active_child_profile is not None else None,
        "completed_story_titles": completed_story_titles,
        "current_streak_days": account_streak,
        "active_plan_count": active_plan_count,
        "completed_plan_sessions": completed_plan_sessions,
    }
    return "Your Buddybug family week", summary_payload, child_summaries


def _replace_child_summaries(
    session: Session,
    *,
    family_digest: FamilyDigest,
    child_summaries: list[FamilyDigestChildSummary],
) -> list[FamilyDigestChildSummary]:
    existing = _list_child_summaries(session, family_digest_id=family_digest.id)
    for item in existing:
        session.delete(item)
    session.commit()

    persisted: list[FamilyDigestChildSummary] = []
    for item in child_summaries:
        item.family_digest_id = family_digest.id
        session.add(item)
        session.commit()
        session.refresh(item)
        persisted.append(item)
    return persisted


def generate_weekly_family_digest(
    session: Session,
    *,
    user: User,
    period_start: date | None = None,
    period_end: date | None = None,
    force_regenerate: bool = False,
) -> tuple[FamilyDigest, list[FamilyDigestChildSummary], bool]:
    resolved_start, resolved_end = (
        (period_start, period_end) if period_start is not None and period_end is not None else get_week_window()
    )
    existing = _get_digest_for_period(
        session,
        user_id=user.id,
        digest_type=FAMILY_DIGEST_TYPE_WEEKLY,
        period_start=resolved_start,
        period_end=resolved_end,
    )
    if existing is not None and not force_regenerate:
        return existing, _list_child_summaries(session, family_digest_id=existing.id), False

    title, summary_payload, child_summaries = build_family_digest_payload(
        session,
        user=user,
        period_start=resolved_start,
        period_end=resolved_end,
    )
    summary_json = _serialize_summary(summary_payload)

    if existing is None:
        digest = FamilyDigest(
            user_id=user.id,
            digest_type=FAMILY_DIGEST_TYPE_WEEKLY,
            period_start=resolved_start,
            period_end=resolved_end,
            title=title,
            summary_json=summary_json,
            generated_at=utc_now(),
        )
    else:
        digest = existing
        digest.title = title
        digest.summary_json = summary_json
        digest.generated_at = utc_now()
        digest.updated_at = utc_now()

    session.add(digest)
    session.commit()
    session.refresh(digest)
    persisted_children = _replace_child_summaries(session, family_digest=digest, child_summaries=child_summaries)
    return digest, persisted_children, True


def get_or_generate_latest_family_digest(
    session: Session,
    *,
    user: User,
) -> tuple[FamilyDigest, list[FamilyDigestChildSummary], bool]:
    return generate_weekly_family_digest(session, user=user)


def list_family_digest_history_for_user(
    session: Session,
    *,
    user_id: int,
    limit: int,
) -> list[FamilyDigest]:
    statement = (
        select(FamilyDigest)
        .where(FamilyDigest.user_id == user_id, FamilyDigest.digest_type == FAMILY_DIGEST_TYPE_WEEKLY)
        .order_by(FamilyDigest.period_end.desc(), FamilyDigest.generated_at.desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_family_digest_detail(
    session: Session,
    *,
    digest_id: int,
    user: User,
) -> tuple[FamilyDigest, list[FamilyDigestChildSummary]]:
    digest = session.get(FamilyDigest, digest_id)
    if digest is None or digest.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family digest not found")
    return digest, _list_child_summaries(session, family_digest_id=digest.id)


def get_family_digest_summary_card(
    session: Session,
    *,
    user: User,
) -> tuple[FamilyDigestSummaryCardResponse, bool]:
    digest, child_summaries, generated_now = get_or_generate_latest_family_digest(session, user=user)
    summary_payload = _parse_summary_json(digest.summary_json)
    return (
        FamilyDigestSummaryCardResponse(
            title=digest.title,
            highlight_text=str(summary_payload.get("highlight_text") or "A gentle Buddybug summary is ready."),
            period_start=digest.period_start,
            period_end=digest.period_end,
            child_count=len(child_summaries),
            stories_completed=int(summary_payload.get("stories_completed") or 0),
            achievements_earned=int(summary_payload.get("achievements_earned") or 0),
        ),
        generated_now,
    )
