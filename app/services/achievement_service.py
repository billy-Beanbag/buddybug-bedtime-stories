from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import or_
from sqlmodel import Session, select

from app.models import (
    AchievementDefinition,
    ChildProfile,
    EarnedAchievement,
    ReadingProgress,
    ReadingStreakSnapshot,
    User,
    UserLibraryItem,
)
from app.schemas.achievement_schema import AchievementDashboardResponse, EarnedAchievementRead
from app.services.analytics_service import track_event_safe
from app.services.review_service import utc_now

ACHIEVEMENT_TARGET_SCOPES = {"user", "child_profile"}

DEFAULT_ACHIEVEMENT_DEFINITIONS = [
    {
        "key": "first_story_completed",
        "title": "First Story Finished",
        "description": "A gentle first finish for story time together.",
        "icon_key": "storybook_star",
        "target_scope": "child_profile",
    },
    {
        "key": "three_stories_completed",
        "title": "Three Stories Shared",
        "description": "A lovely rhythm is starting to form.",
        "icon_key": "moon_stack",
        "target_scope": "child_profile",
    },
    {
        "key": "seven_day_reading_streak",
        "title": "Seven Cozy Days",
        "description": "Seven reading days in a row is a beautiful family habit.",
        "icon_key": "calendar_glow",
        "target_scope": "child_profile",
    },
    {
        "key": "first_saved_story",
        "title": "First Story Saved",
        "description": "A story has been tucked away for later.",
        "icon_key": "bookmark_heart",
        "target_scope": "child_profile",
    },
    {
        "key": "first_narrated_story",
        "title": "First Narrated Story",
        "description": "A narrated story has joined the bedtime routine.",
        "icon_key": "sparkle_speaker",
        "target_scope": "child_profile",
    },
    {
        "key": "bedtime_routine_started",
        "title": "Bedtime Rhythm Started",
        "description": "Reading has happened across a few calm evenings already.",
        "icon_key": "moon_path",
        "target_scope": "child_profile",
    },
    {
        "key": "family_library_started",
        "title": "Family Library Started",
        "description": "The family library is beginning to feel like home.",
        "icon_key": "library_shelf",
        "target_scope": "user",
    },
]

CHILD_SCOPE_MILESTONE_ORDER = [
    "first_story_completed",
    "three_stories_completed",
    "bedtime_routine_started",
    "first_saved_story",
    "first_narrated_story",
    "seven_day_reading_streak",
]
USER_SCOPE_MILESTONE_ORDER = [
    "first_story_completed",
    "three_stories_completed",
    "first_saved_story",
    "first_narrated_story",
    "bedtime_routine_started",
    "seven_day_reading_streak",
    "family_library_started",
]


@dataclass
class EarnedAchievementBundle:
    earned: EarnedAchievement
    definition: AchievementDefinition


def seed_achievement_definitions(session: Session) -> None:
    existing = {item.key for item in session.exec(select(AchievementDefinition)).all()}
    created_any = False
    for payload in DEFAULT_ACHIEVEMENT_DEFINITIONS:
        if payload["key"] in existing:
            continue
        session.add(AchievementDefinition(**payload, is_active=True))
        created_any = True
    if created_any:
        session.commit()


def get_achievement_definitions(session: Session, *, active_only: bool = True) -> list[AchievementDefinition]:
    statement = select(AchievementDefinition).order_by(AchievementDefinition.id.asc())
    if active_only:
        statement = statement.where(AchievementDefinition.is_active.is_(True))
    return list(session.exec(statement).all())


def get_achievement_definition_by_key(
    session: Session,
    *,
    key: str,
    active_only: bool = True,
) -> AchievementDefinition | None:
    statement = select(AchievementDefinition).where(AchievementDefinition.key == key)
    if active_only:
        statement = statement.where(AchievementDefinition.is_active.is_(True))
    return session.exec(statement).first()


def validate_achievement_target_scope(target_scope: str) -> str:
    if target_scope not in ACHIEVEMENT_TARGET_SCOPES:
        raise ValueError(f"Unsupported achievement target scope: {target_scope}")
    return target_scope


def _get_earned_achievement(
    session: Session,
    *,
    achievement_definition_id: int,
    user_id: int,
    child_profile_id: int | None,
) -> EarnedAchievement | None:
    statement = select(EarnedAchievement).where(
        EarnedAchievement.achievement_definition_id == achievement_definition_id,
        EarnedAchievement.user_id == user_id,
    )
    if child_profile_id is None:
        statement = statement.where(EarnedAchievement.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(EarnedAchievement.child_profile_id == child_profile_id)
    return session.exec(statement).first()


def award_achievement_if_missing(
    session: Session,
    *,
    achievement_key: str,
    user: User,
    child_profile_id: int | None = None,
    source_table: str | None = None,
    source_id: str | None = None,
    earned_at: datetime | None = None,
) -> EarnedAchievement | None:
    definition = get_achievement_definition_by_key(session, key=achievement_key)
    if definition is None:
        return None

    existing = _get_earned_achievement(
        session,
        achievement_definition_id=definition.id,
        user_id=user.id,
        child_profile_id=child_profile_id,
    )
    if existing is not None:
        return existing

    earned = EarnedAchievement(
        achievement_definition_id=definition.id,
        user_id=user.id,
        child_profile_id=child_profile_id,
        earned_at=earned_at or utc_now(),
        source_table=source_table,
        source_id=source_id,
    )
    session.add(earned)
    session.commit()
    session.refresh(earned)
    track_event_safe(
        session,
        event_name="achievement_earned",
        user=user,
        child_profile_id=child_profile_id,
        metadata={
            "achievement_key": definition.key,
            "achievement_title": definition.title,
            "target_scope": definition.target_scope,
            "source_table": source_table,
            "source_id": source_id,
        },
    )
    return earned


def _get_child_profile_ids_for_user(session: Session, *, user_id: int) -> list[int]:
    statement = select(ChildProfile.id).where(ChildProfile.user_id == user_id)
    return [item for item in session.exec(statement).all()]


def _progress_rows_for_scope(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
) -> list[ReadingProgress]:
    if child_profile_id is not None:
        statement = select(ReadingProgress).where(ReadingProgress.child_profile_id == child_profile_id)
        return list(session.exec(statement).all())

    child_ids = _get_child_profile_ids_for_user(session, user_id=user_id)
    statement = select(ReadingProgress)
    if child_ids:
        statement = statement.where(
            or_(
                ReadingProgress.child_profile_id.in_(child_ids),
                (
                    (ReadingProgress.reader_identifier == f"user:{user_id}")
                    & (ReadingProgress.child_profile_id == None)  # noqa: E711
                ),
            )
        )
    else:
        statement = statement.where(
            ReadingProgress.reader_identifier == f"user:{user_id}",
            ReadingProgress.child_profile_id == None,  # noqa: E711
        )
    return list(session.exec(statement).all())


def _saved_items_for_scope(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
) -> list[UserLibraryItem]:
    statement = select(UserLibraryItem).where(
        UserLibraryItem.user_id == user_id,
        UserLibraryItem.status == "saved",
    )
    if child_profile_id is None:
        return list(session.exec(statement).all())
    return list(session.exec(statement.where(UserLibraryItem.child_profile_id == child_profile_id)).all())


def _completed_story_count(session: Session, *, user_id: int, child_profile_id: int | None) -> int:
    return sum(1 for item in _progress_rows_for_scope(session, user_id=user_id, child_profile_id=child_profile_id) if item.completed)


def _saved_story_count(session: Session, *, user_id: int, child_profile_id: int | None) -> int:
    return len(_saved_items_for_scope(session, user_id=user_id, child_profile_id=child_profile_id))


def _distinct_read_dates(session: Session, *, user_id: int, child_profile_id: int | None) -> list[date]:
    dates = {
        progress.last_opened_at.date()
        for progress in _progress_rows_for_scope(session, user_id=user_id, child_profile_id=child_profile_id)
    }
    return sorted(dates)


def _calculate_streak_from_dates(read_dates: list[date]) -> tuple[int, int, date | None]:
    if not read_dates:
        return 0, 0, None

    sorted_dates = sorted(set(read_dates))
    current_streak = 1
    longest_streak = 1
    running = 1
    for index in range(1, len(sorted_dates)):
        if sorted_dates[index] == sorted_dates[index - 1] + timedelta(days=1):
            running += 1
        else:
            running = 1
        longest_streak = max(longest_streak, running)

    last_date = sorted_dates[-1]
    current_streak = 1
    for index in range(len(sorted_dates) - 2, -1, -1):
        if sorted_dates[index] == sorted_dates[index + 1] - timedelta(days=1):
            current_streak += 1
        else:
            break
    return current_streak, longest_streak, last_date


def _get_streak_snapshot(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
) -> ReadingStreakSnapshot | None:
    statement = select(ReadingStreakSnapshot).where(ReadingStreakSnapshot.user_id == user_id)
    if child_profile_id is None:
        statement = statement.where(ReadingStreakSnapshot.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(ReadingStreakSnapshot.child_profile_id == child_profile_id)
    return session.exec(statement).first()


def _upsert_streak_snapshot(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
    current_streak_days: int,
    longest_streak_days: int,
    last_read_date: date | None,
) -> ReadingStreakSnapshot:
    snapshot = _get_streak_snapshot(session, user_id=user_id, child_profile_id=child_profile_id)
    if snapshot is None:
        snapshot = ReadingStreakSnapshot(
            user_id=user_id,
            child_profile_id=child_profile_id,
            current_streak_days=current_streak_days,
            longest_streak_days=longest_streak_days,
            last_read_date=last_read_date,
        )
    else:
        snapshot.current_streak_days = current_streak_days
        snapshot.longest_streak_days = longest_streak_days
        snapshot.last_read_date = last_read_date
        snapshot.updated_at = utc_now()
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def _track_streak_if_changed(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None,
    before: ReadingStreakSnapshot | None,
    after: ReadingStreakSnapshot,
) -> None:
    if (
        before is not None
        and before.current_streak_days == after.current_streak_days
        and before.longest_streak_days == after.longest_streak_days
        and before.last_read_date == after.last_read_date
    ):
        return
    track_event_safe(
        session,
        event_name="streak_updated",
        user=user,
        child_profile_id=child_profile_id,
        metadata={
            "current_streak_days": after.current_streak_days,
            "longest_streak_days": after.longest_streak_days,
            "last_read_date": after.last_read_date.isoformat() if after.last_read_date else None,
        },
    )


def _compute_incremental_streak(
    before: ReadingStreakSnapshot | None,
    *,
    read_day: date,
) -> tuple[int, int, date]:
    if before is None or before.last_read_date is None:
        return 1, 1, read_day
    if before.last_read_date == read_day:
        return before.current_streak_days, before.longest_streak_days, before.last_read_date
    if before.last_read_date == read_day - timedelta(days=1):
        current_streak = before.current_streak_days + 1
    else:
        current_streak = 1
    longest_streak = max(before.longest_streak_days, current_streak)
    return current_streak, longest_streak, read_day


def update_reading_streak(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
    read_at: datetime | None = None,
) -> ReadingStreakSnapshot:
    effective_read_at = read_at or utc_now()
    read_day = effective_read_at.date()

    account_before = _get_streak_snapshot(session, user_id=user.id, child_profile_id=None)
    account_current, account_longest, account_last_date = _compute_incremental_streak(
        account_before,
        read_day=read_day,
    )
    account_snapshot = _upsert_streak_snapshot(
        session,
        user_id=user.id,
        child_profile_id=None,
        current_streak_days=account_current,
        longest_streak_days=account_longest,
        last_read_date=account_last_date,
    )
    _track_streak_if_changed(
        session,
        user=user,
        child_profile_id=None,
        before=account_before,
        after=account_snapshot,
    )

    if child_profile_id is None:
        if account_snapshot.current_streak_days >= 7:
            award_achievement_if_missing(
                session,
                achievement_key="seven_day_reading_streak",
                user=user,
                child_profile_id=None,
                source_table="reading_streak_snapshot",
                source_id=str(account_snapshot.id),
            )
        if account_snapshot.longest_streak_days >= 3:
            award_achievement_if_missing(
                session,
                achievement_key="bedtime_routine_started",
                user=user,
                child_profile_id=None,
                source_table="reading_streak_snapshot",
                source_id=str(account_snapshot.id),
            )
        return account_snapshot

    child_before = _get_streak_snapshot(session, user_id=user.id, child_profile_id=child_profile_id)
    child_current, child_longest, child_last_date = _compute_incremental_streak(
        child_before,
        read_day=read_day,
    )
    child_snapshot = _upsert_streak_snapshot(
        session,
        user_id=user.id,
        child_profile_id=child_profile_id,
        current_streak_days=child_current,
        longest_streak_days=child_longest,
        last_read_date=child_last_date,
    )
    _track_streak_if_changed(
        session,
        user=user,
        child_profile_id=child_profile_id,
        before=child_before,
        after=child_snapshot,
    )
    if child_snapshot.current_streak_days >= 7:
        award_achievement_if_missing(
            session,
            achievement_key="seven_day_reading_streak",
            user=user,
            child_profile_id=child_profile_id,
            source_table="reading_streak_snapshot",
            source_id=str(child_snapshot.id),
        )
    if child_snapshot.longest_streak_days >= 3:
        award_achievement_if_missing(
            session,
            achievement_key="bedtime_routine_started",
            user=user,
            child_profile_id=child_profile_id,
            source_table="reading_streak_snapshot",
            source_id=str(child_snapshot.id),
        )
    return child_snapshot


def handle_story_completed(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
    source_table: str | None = None,
    source_id: str | None = None,
    occurred_at: datetime | None = None,
) -> list[EarnedAchievement]:
    earned: list[EarnedAchievement] = []
    snapshot = update_reading_streak(session, user=user, child_profile_id=child_profile_id, read_at=occurred_at)
    completed_count = _completed_story_count(session, user_id=user.id, child_profile_id=child_profile_id)
    if completed_count >= 1:
        item = award_achievement_if_missing(
            session,
            achievement_key="first_story_completed",
            user=user,
            child_profile_id=child_profile_id,
            source_table=source_table or "readingprogress",
            source_id=source_id or str(snapshot.id),
            earned_at=occurred_at,
        )
        if item is not None:
            earned.append(item)
    if completed_count >= 3:
        item = award_achievement_if_missing(
            session,
            achievement_key="three_stories_completed",
            user=user,
            child_profile_id=child_profile_id,
            source_table=source_table or "readingprogress",
            source_id=source_id or str(snapshot.id),
            earned_at=occurred_at,
        )
        if item is not None:
            earned.append(item)
    return earned


def handle_story_saved(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
    source_table: str | None = None,
    source_id: str | None = None,
) -> list[EarnedAchievement]:
    earned: list[EarnedAchievement] = []
    saved_count = _saved_story_count(session, user_id=user.id, child_profile_id=child_profile_id)
    if saved_count >= 1:
        item = award_achievement_if_missing(
            session,
            achievement_key="first_saved_story",
            user=user,
            child_profile_id=child_profile_id,
            source_table=source_table or "userlibraryitem",
            source_id=source_id,
        )
        if item is not None:
            earned.append(item)
    aggregate_saved_count = _saved_story_count(session, user_id=user.id, child_profile_id=None)
    if aggregate_saved_count >= 3:
        item = award_achievement_if_missing(
            session,
            achievement_key="family_library_started",
            user=user,
            child_profile_id=None,
            source_table=source_table or "userlibraryitem",
            source_id=source_id,
        )
        if item is not None:
            earned.append(item)
    return earned


def handle_narrated_story_started(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
    source_table: str | None = None,
    source_id: str | None = None,
) -> EarnedAchievement | None:
    return award_achievement_if_missing(
        session,
        achievement_key="first_narrated_story",
        user=user,
        child_profile_id=child_profile_id,
        source_table=source_table or "booknarration",
        source_id=source_id,
    )


def _build_earned_achievement_reads(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
) -> list[EarnedAchievementRead]:
    statement = select(EarnedAchievement).where(EarnedAchievement.user_id == user_id)
    if child_profile_id is None:
        earned_items = list(session.exec(statement.order_by(EarnedAchievement.earned_at.desc())).all())
    else:
        earned_items = list(
            session.exec(
                statement.where(
                    or_(
                        EarnedAchievement.child_profile_id == child_profile_id,
                        EarnedAchievement.child_profile_id == None,  # noqa: E711
                    )
                ).order_by(EarnedAchievement.earned_at.desc())
            ).all()
        )

    definitions = {
        item.id: item
        for item in get_achievement_definitions(session, active_only=False)
    }
    reads: list[EarnedAchievementRead] = []
    for earned in earned_items:
        definition = definitions.get(earned.achievement_definition_id)
        reads.append(
            EarnedAchievementRead(
                id=earned.id,
                achievement_definition_id=earned.achievement_definition_id,
                user_id=earned.user_id,
                child_profile_id=earned.child_profile_id,
                earned_at=earned.earned_at,
                source_table=earned.source_table,
                source_id=earned.source_id,
                created_at=earned.created_at,
                updated_at=earned.updated_at,
                achievement_key=definition.key if definition is not None else None,
                title=definition.title if definition is not None else None,
                description=definition.description if definition is not None else None,
                icon_key=definition.icon_key if definition is not None else None,
                target_scope=definition.target_scope if definition is not None else None,
            )
        )
    if child_profile_id is not None:
        reads.sort(key=lambda item: (item.child_profile_id != child_profile_id, item.earned_at), reverse=True)
    return reads


def _get_or_compute_streak_snapshot(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
) -> ReadingStreakSnapshot:
    existing = _get_streak_snapshot(session, user_id=user_id, child_profile_id=child_profile_id)
    if existing is not None:
        return existing
    read_dates = _distinct_read_dates(session, user_id=user_id, child_profile_id=child_profile_id)
    current_streak, longest_streak, last_read_date = _calculate_streak_from_dates(read_dates)
    return _upsert_streak_snapshot(
        session,
        user_id=user_id,
        child_profile_id=child_profile_id,
        current_streak_days=current_streak,
        longest_streak_days=longest_streak,
        last_read_date=last_read_date,
    )


def _next_milestone_title(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
) -> str | None:
    earned_reads = _build_earned_achievement_reads(session, user_id=user_id, child_profile_id=child_profile_id)
    earned_keys = {item.achievement_key for item in earned_reads if item.achievement_key}
    ordered_keys = CHILD_SCOPE_MILESTONE_ORDER if child_profile_id is not None else USER_SCOPE_MILESTONE_ORDER
    for key in ordered_keys:
        if key in earned_keys:
            continue
        definition = get_achievement_definition_by_key(session, key=key)
        if definition is not None:
            return definition.title
    return None


def get_earned_achievements_for_user(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
) -> list[EarnedAchievementRead]:
    return _build_earned_achievement_reads(session, user_id=user_id, child_profile_id=child_profile_id)


def get_achievement_dashboard(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
) -> AchievementDashboardResponse:
    snapshot = _get_or_compute_streak_snapshot(session, user_id=user.id, child_profile_id=child_profile_id)
    return AchievementDashboardResponse(
        earned_achievements=_build_earned_achievement_reads(
            session,
            user_id=user.id,
            child_profile_id=child_profile_id,
        ),
        current_streak=snapshot.current_streak_days,
        longest_streak=snapshot.longest_streak_days,
        next_suggested_milestone=_next_milestone_title(
            session,
            user_id=user.id,
            child_profile_id=child_profile_id,
        ),
    )


def rebuild_achievements_for_user(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
) -> AchievementDashboardResponse:
    scopes = [child_profile_id] if child_profile_id is not None else [None, *_get_child_profile_ids_for_user(session, user_id=user.id)]
    for scope_child_profile_id in scopes:
        _get_or_compute_streak_snapshot(session, user_id=user.id, child_profile_id=scope_child_profile_id)
        completed_count = _completed_story_count(session, user_id=user.id, child_profile_id=scope_child_profile_id)
        saved_count = _saved_story_count(session, user_id=user.id, child_profile_id=scope_child_profile_id)
        snapshot = _get_or_compute_streak_snapshot(session, user_id=user.id, child_profile_id=scope_child_profile_id)

        if completed_count >= 1:
            award_achievement_if_missing(session, achievement_key="first_story_completed", user=user, child_profile_id=scope_child_profile_id)
        if completed_count >= 3:
            award_achievement_if_missing(session, achievement_key="three_stories_completed", user=user, child_profile_id=scope_child_profile_id)
        if saved_count >= 1:
            award_achievement_if_missing(session, achievement_key="first_saved_story", user=user, child_profile_id=scope_child_profile_id)
        if scope_child_profile_id is None and saved_count >= 3:
            award_achievement_if_missing(session, achievement_key="family_library_started", user=user, child_profile_id=None)
        if snapshot.longest_streak_days >= 3:
            award_achievement_if_missing(session, achievement_key="bedtime_routine_started", user=user, child_profile_id=scope_child_profile_id)
        if snapshot.current_streak_days >= 7:
            award_achievement_if_missing(session, achievement_key="seven_day_reading_streak", user=user, child_profile_id=scope_child_profile_id)
    return get_achievement_dashboard(session, user=user, child_profile_id=child_profile_id)
