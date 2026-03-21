from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    AnalyticsEvent,
    Book,
    ChildProfile,
    DailyStorySuggestion,
    ReadingProgress,
    ReengagementSuggestion,
    User,
    UserEngagementState,
    UserLibraryItem,
)
from app.services.subscription_service import has_premium_access

REENGAGEMENT_STATE_KEYS = {
    "active",
    "new_but_inactive",
    "partially_activated",
    "dormant_7d",
    "dormant_30d",
    "lapsed_premium",
    "preview_only_user",
    "unfinished_story_user",
    "saved_but_unread_user",
}
SUGGESTION_TYPES = {
    "continue_story",
    "revisit_saved_story",
    "daily_pick_return",
    "premium_upgrade_reminder",
    "lapsed_premium_return",
    "child_profile_setup_reminder",
}
REENGAGEMENT_REFRESH_INTERVAL = timedelta(hours=12)
MEANINGFUL_ACTIVITY_EVENT_NAMES = {
    "app_opened",
    "library_viewed",
    "book_opened",
    "book_completed",
    "onboarding_completed",
    "onboarding_first_story_opened",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass
class SuggestedCard:
    suggestion_type: str
    title: str
    body: str
    child_profile_id: int | None = None
    related_book_id: int | None = None
    state_key: str | None = None


@dataclass
class EngagementSignals:
    last_active_at: datetime | None
    last_story_opened_at: datetime | None
    last_story_completed_at: datetime | None
    last_subscription_active_at: datetime | None
    active_child_profiles_count: int
    unread_saved_books_count: int
    unfinished_books_count: int
    preview_only_books_count: int
    newest_unfinished_progress: ReadingProgress | None
    newest_unread_saved_item: UserLibraryItem | None
    primary_child_profile: ChildProfile | None
    daily_story_suggestion: DailyStorySuggestion | None
    latest_meaningful_event_at: datetime | None


def validate_engagement_state_key(state_key: str) -> str:
    if state_key not in REENGAGEMENT_STATE_KEYS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid engagement state key")
    return state_key


def validate_suggestion_type(suggestion_type: str) -> str:
    if suggestion_type not in SUGGESTION_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reengagement suggestion type")
    return suggestion_type


def get_user_engagement_state(session: Session, *, user_id: int) -> UserEngagementState | None:
    return session.exec(select(UserEngagementState).where(UserEngagementState.user_id == user_id)).first()


def list_reengagement_suggestions_for_user(
    session: Session,
    *,
    user_id: int,
    include_dismissed: bool = False,
) -> list[ReengagementSuggestion]:
    statement = (
        select(ReengagementSuggestion)
        .where(ReengagementSuggestion.user_id == user_id)
        .order_by(ReengagementSuggestion.created_at.desc(), ReengagementSuggestion.id.desc())
    )
    if not include_dismissed:
        statement = statement.where(ReengagementSuggestion.is_dismissed.is_(False))
    return list(session.exec(statement).all())


def get_reengagement_suggestion_or_404(session: Session, *, suggestion_id: int) -> ReengagementSuggestion:
    suggestion = session.get(ReengagementSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reengagement suggestion not found")
    return suggestion


def derive_state_key(*, user: User, signals: EngagementSignals) -> str:
    last_active_at = signals.last_active_at
    now = utc_now()

    if _is_lapsed_premium(user=user, signals=signals):
        return "lapsed_premium"
    if _is_new_but_inactive(user=user, signals=signals):
        return "new_but_inactive"
    if last_active_at is not None and last_active_at <= now - timedelta(days=30):
        return "dormant_30d"
    if last_active_at is not None and last_active_at <= now - timedelta(days=7):
        return "dormant_7d"
    if signals.preview_only_books_count > 0 and not has_premium_access(user):
        return "preview_only_user"
    if signals.unfinished_books_count > 0:
        return "unfinished_story_user"
    if signals.unread_saved_books_count > 0:
        return "saved_but_unread_user"
    if _is_partially_activated(signals=signals):
        return "partially_activated"
    return "active"


def rebuild_user_engagement_state(session: Session, *, user: User) -> UserEngagementState:
    signals = _collect_engagement_signals(session, user=user)
    existing = get_user_engagement_state(session, user_id=user.id)
    generated_at = utc_now()
    state_key = derive_state_key(user=user, signals=signals)

    if existing is None:
        existing = UserEngagementState(user_id=user.id)

    existing.state_key = state_key
    existing.last_active_at = signals.last_active_at
    existing.last_story_opened_at = signals.last_story_opened_at
    existing.last_story_completed_at = signals.last_story_completed_at
    existing.last_subscription_active_at = signals.last_subscription_active_at
    existing.active_child_profiles_count = signals.active_child_profiles_count
    existing.unread_saved_books_count = signals.unread_saved_books_count
    existing.unfinished_books_count = signals.unfinished_books_count
    existing.preview_only_books_count = signals.preview_only_books_count
    existing.generated_at = generated_at
    existing.updated_at = generated_at
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


def generate_reengagement_suggestions(
    session: Session,
    *,
    user: User,
    engagement_state: UserEngagementState,
) -> list[ReengagementSuggestion]:
    signals = _collect_engagement_signals(session, user=user)
    desired_cards = _build_desired_cards(session, user=user, engagement_state=engagement_state, signals=signals)
    existing = list_reengagement_suggestions_for_user(session, user_id=user.id, include_dismissed=True)

    active_by_key = {_suggestion_key(item): item for item in existing if not item.is_dismissed}
    dismissed_keys = {_suggestion_key(item) for item in existing if item.is_dismissed}
    desired_by_key = {_card_key(card): card for card in desired_cards}

    for key, current in active_by_key.items():
        if key in desired_by_key:
            card = desired_by_key[key]
            current.title = card.title
            current.body = card.body
            current.state_key = card.state_key
            current.updated_at = utc_now()
            session.add(current)
        else:
            session.delete(current)

    for key, card in desired_by_key.items():
        if key in active_by_key or key in dismissed_keys:
            continue
        session.add(
            ReengagementSuggestion(
                user_id=user.id,
                child_profile_id=card.child_profile_id,
                suggestion_type=validate_suggestion_type(card.suggestion_type),
                title=card.title,
                body=card.body,
                related_book_id=card.related_book_id,
                state_key=card.state_key,
            )
        )

    session.commit()
    return list_reengagement_suggestions_for_user(session, user_id=user.id, include_dismissed=False)


def get_reengagement_dashboard(
    session: Session,
    *,
    user: User,
    force_rebuild: bool = False,
) -> tuple[UserEngagementState, list[ReengagementSuggestion]]:
    state = get_user_engagement_state(session, user_id=user.id)
    now = utc_now()
    needs_refresh = (
        force_rebuild
        or state is None
        or state.generated_at is None
        or _normalize_datetime(state.generated_at) <= now - REENGAGEMENT_REFRESH_INTERVAL
    )
    if needs_refresh:
        state = rebuild_user_engagement_state(session, user=user)
        suggestions = generate_reengagement_suggestions(session, user=user, engagement_state=state)
        return state, suggestions
    return state, list_reengagement_suggestions_for_user(session, user_id=user.id, include_dismissed=False)


def dismiss_reengagement_suggestion(
    session: Session,
    *,
    suggestion: ReengagementSuggestion,
    is_dismissed: bool,
) -> ReengagementSuggestion:
    suggestion.is_dismissed = is_dismissed
    suggestion.updated_at = utc_now()
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    return suggestion


def list_engagement_states_for_admin(
    session: Session,
    *,
    state_key: str | None = None,
    limit: int = 100,
) -> list[UserEngagementState]:
    statement = select(UserEngagementState).order_by(UserEngagementState.generated_at.desc()).limit(limit)
    if state_key is not None:
        statement = statement.where(UserEngagementState.state_key == validate_engagement_state_key(state_key))
    return list(session.exec(statement).all())


def list_reengagement_suggestions_for_admin(
    session: Session,
    *,
    suggestion_type: str | None = None,
    state_key: str | None = None,
    limit: int = 100,
) -> list[ReengagementSuggestion]:
    statement = (
        select(ReengagementSuggestion)
        .order_by(ReengagementSuggestion.created_at.desc(), ReengagementSuggestion.id.desc())
        .limit(limit)
    )
    if suggestion_type is not None:
        statement = statement.where(ReengagementSuggestion.suggestion_type == validate_suggestion_type(suggestion_type))
    if state_key is not None:
        statement = statement.where(ReengagementSuggestion.state_key == validate_engagement_state_key(state_key))
    return list(session.exec(statement).all())


def _collect_engagement_signals(session: Session, *, user: User) -> EngagementSignals:
    active_child_profiles = list(
        session.exec(
            select(ChildProfile)
            .where(ChildProfile.user_id == user.id, ChildProfile.is_active.is_(True))
            .order_by(ChildProfile.updated_at.desc(), ChildProfile.id.desc())
        ).all()
    )
    primary_child_profile = active_child_profiles[0] if active_child_profiles else None

    reader_identifier = f"user:{user.id}"
    progresses = list(
        session.exec(
            select(ReadingProgress)
            .where(ReadingProgress.reader_identifier == reader_identifier)
            .order_by(ReadingProgress.last_opened_at.desc(), ReadingProgress.updated_at.desc())
        ).all()
    )
    completed_progresses = [progress for progress in progresses if progress.completed]
    unfinished_progresses = [progress for progress in progresses if not progress.completed and progress.current_page_number > 0]

    saved_items = list(
        session.exec(
            select(UserLibraryItem)
            .where(UserLibraryItem.user_id == user.id, UserLibraryItem.status == "saved")
            .order_by(UserLibraryItem.updated_at.desc(), UserLibraryItem.id.desc())
        ).all()
    )

    preview_events = list(
        session.exec(
            select(AnalyticsEvent)
            .where(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.event_name == "preview_wall_hit",
            )
            .order_by(AnalyticsEvent.occurred_at.desc())
        ).all()
    )
    meaningful_events = list(
        session.exec(
            select(AnalyticsEvent)
            .where(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.event_name.in_(tuple(MEANINGFUL_ACTIVITY_EVENT_NAMES)),
            )
            .order_by(AnalyticsEvent.occurred_at.desc())
        ).all()
    )

    completed_book_ids = {progress.book_id for progress in completed_progresses}
    preview_only_books_count = len(
        {
            event.book_id
            for event in preview_events
            if event.book_id is not None and event.book_id not in completed_book_ids
        }
    )
    unread_saved_items = [
        item
        for item in saved_items
        if item.last_opened_at is None and item.book_id not in completed_book_ids
    ]

    newest_unfinished_progress = unfinished_progresses[0] if unfinished_progresses else None
    newest_unread_saved_item = unread_saved_items[0] if unread_saved_items else None
    latest_meaningful_event_at = _max_datetime(*[_normalize_datetime(event.occurred_at) for event in meaningful_events])
    last_story_opened_at = _max_datetime(*[_normalize_datetime(progress.last_opened_at) for progress in progresses])
    last_story_completed_at = _max_datetime(
        *[_normalize_datetime(progress.updated_at or progress.last_opened_at) for progress in completed_progresses]
    )

    library_opened_at = _max_datetime(*[_normalize_datetime(item.last_opened_at) for item in saved_items])
    last_active_at = _max_datetime(last_story_opened_at, last_story_completed_at, latest_meaningful_event_at, library_opened_at)
    if last_active_at is None:
        last_active_at = _normalize_datetime(user.created_at)

    daily_story_suggestion = _get_daily_story_suggestion(session, user_id=user.id, child_profile=primary_child_profile)

    return EngagementSignals(
        last_active_at=last_active_at,
        last_story_opened_at=last_story_opened_at,
        last_story_completed_at=last_story_completed_at,
        last_subscription_active_at=_last_subscription_active_at(user),
        active_child_profiles_count=len(active_child_profiles),
        unread_saved_books_count=len(unread_saved_items),
        unfinished_books_count=len(unfinished_progresses),
        preview_only_books_count=preview_only_books_count,
        newest_unfinished_progress=newest_unfinished_progress,
        newest_unread_saved_item=newest_unread_saved_item,
        primary_child_profile=primary_child_profile,
        daily_story_suggestion=daily_story_suggestion,
        latest_meaningful_event_at=latest_meaningful_event_at,
    )


def _build_desired_cards(
    session: Session,
    *,
    user: User,
    engagement_state: UserEngagementState,
    signals: EngagementSignals,
) -> list[SuggestedCard]:
    cards: list[SuggestedCard] = []

    if signals.newest_unfinished_progress is not None:
        book = session.get(Book, signals.newest_unfinished_progress.book_id)
        if book is not None:
            cards.append(
                SuggestedCard(
                    suggestion_type="continue_story",
                    title=f"Finish {book.title}",
                    body="Pick up where you left off and keep tonight's reading session easy.",
                    child_profile_id=signals.newest_unfinished_progress.child_profile_id,
                    related_book_id=book.id,
                    state_key=engagement_state.state_key,
                )
            )

    if signals.newest_unread_saved_item is not None:
        book = session.get(Book, signals.newest_unread_saved_item.book_id)
        if book is not None:
            cards.append(
                SuggestedCard(
                    suggestion_type="revisit_saved_story",
                    title=f"Read your saved story: {book.title}",
                    body="You already picked this one out. Open it tonight and turn that saved story into a real session.",
                    child_profile_id=signals.newest_unread_saved_item.child_profile_id,
                    related_book_id=book.id,
                    state_key=engagement_state.state_key,
                )
            )

    if engagement_state.state_key in {"dormant_7d", "dormant_30d"} and signals.daily_story_suggestion is not None:
        book = session.get(Book, signals.daily_story_suggestion.book_id)
        if book is not None:
            cards.append(
                SuggestedCard(
                    suggestion_type="daily_pick_return",
                    title="Your next bedtime pick is ready",
                    body=f"Come back with {book.title} and make tonight's story choice easier.",
                    child_profile_id=signals.daily_story_suggestion.child_profile_id,
                    related_book_id=book.id,
                    state_key=engagement_state.state_key,
                )
            )

    if signals.preview_only_books_count > 0 and not has_premium_access(user):
        cards.append(
            SuggestedCard(
                suggestion_type="premium_upgrade_reminder",
                title="Unlock full stories and narration",
                body="You have already sampled Buddybug stories. Premium opens full reads, audio, and offline convenience.",
                state_key=engagement_state.state_key,
            )
        )

    if engagement_state.state_key == "lapsed_premium":
        cards.append(
            SuggestedCard(
                suggestion_type="lapsed_premium_return",
                title="Come back to Buddybug Premium",
                body="Restore premium access to unlock full stories, narration, and your calmer evening reading routine again.",
                state_key=engagement_state.state_key,
            )
        )

    if signals.active_child_profiles_count == 0:
        cards.append(
            SuggestedCard(
                suggestion_type="child_profile_setup_reminder",
                title="Set up a child profile",
                body="A child profile helps Buddybug pick the right age band, language, and bedtime recommendations.",
                state_key=engagement_state.state_key,
            )
        )

    return cards


def _is_new_but_inactive(*, user: User, signals: EngagementSignals) -> bool:
    created_at = _normalize_datetime(user.created_at)
    if created_at is None:
        return False
    if created_at <= utc_now() - timedelta(days=14):
        return False
    return (
        signals.last_story_opened_at is None
        and signals.last_story_completed_at is None
        and signals.active_child_profiles_count == 0
    )


def _is_partially_activated(*, signals: EngagementSignals) -> bool:
    return (
        signals.last_story_completed_at is None
        and (signals.active_child_profiles_count > 0 or signals.last_story_opened_at is not None)
    )


def _is_lapsed_premium(*, user: User, signals: EngagementSignals) -> bool:
    if has_premium_access(user):
        return False
    if signals.last_subscription_active_at is None:
        return False
    return user.subscription_tier == "free" or user.subscription_status in {"expired", "canceled", "past_due"}


def _last_subscription_active_at(user: User) -> datetime | None:
    if has_premium_access(user):
        return _max_datetime(_normalize_datetime(user.subscription_expires_at), _normalize_datetime(user.trial_ends_at), _normalize_datetime(user.updated_at))
    return _max_datetime(_normalize_datetime(user.subscription_expires_at), _normalize_datetime(user.trial_ends_at))


def _get_daily_story_suggestion(
    session: Session,
    *,
    user_id: int,
    child_profile: ChildProfile | None,
) -> DailyStorySuggestion | None:
    statement = select(DailyStorySuggestion).where(DailyStorySuggestion.user_id == user_id)
    if child_profile is not None:
        scoped = session.exec(
            statement.where(DailyStorySuggestion.child_profile_id == child_profile.id).order_by(DailyStorySuggestion.created_at.desc())
        ).first()
        if scoped is not None:
            return scoped
    return session.exec(statement.order_by(DailyStorySuggestion.created_at.desc())).first()


def _max_datetime(*values: datetime | None) -> datetime | None:
    normalized = [value for value in values if value is not None]
    return max(normalized) if normalized else None


def _suggestion_key(suggestion: ReengagementSuggestion) -> tuple[str, int | None, int | None, str | None]:
    return (
        suggestion.suggestion_type,
        suggestion.child_profile_id,
        suggestion.related_book_id,
        suggestion.state_key,
    )


def _card_key(card: SuggestedCard) -> tuple[str, int | None, int | None, str | None]:
    return (
        card.suggestion_type,
        card.child_profile_id,
        card.related_book_id,
        card.state_key,
    )
