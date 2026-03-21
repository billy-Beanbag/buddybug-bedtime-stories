from collections import Counter

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    Book,
    ChildProfile,
    ChildReadingProfile,
    ReadingProgress,
    StoryDraft,
    StoryIdea,
    UserStoryFeedback,
)
from app.services.content_lane_service import validate_content_lane_key
from app.services.i18n_service import validate_language_code
from app.services.review_service import utc_now

SUPPORTED_CHILD_AGE_BANDS = {"3-7", "8-12"}


def _validate_age_band(age_band: str) -> str:
    if age_band not in SUPPORTED_CHILD_AGE_BANDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported child age band")
    return age_band


def _top_values(values: list[str], limit: int = 3) -> str | None:
    cleaned = [value.strip() for value in values if value and value.strip()]
    if not cleaned:
        return None
    return ", ".join(item for item, _count in Counter(cleaned).most_common(limit))


def resolve_child_content_lane(session: Session, *, age_band: str, content_lane_key: str | None) -> str:
    lane = validate_content_lane_key(
        session,
        age_band=_validate_age_band(age_band),
        content_lane_key=content_lane_key,
    )
    return lane.key


def get_child_profiles_for_user(session: Session, *, user_id: int, active_only: bool = False) -> list[ChildProfile]:
    statement = select(ChildProfile).where(ChildProfile.user_id == user_id).order_by(ChildProfile.created_at.asc())
    if active_only:
        statement = statement.where(ChildProfile.is_active.is_(True))
    return list(session.exec(statement).all())


def get_child_profile_for_user(session: Session, *, user_id: int, child_profile_id: int) -> ChildProfile:
    child_profile = session.get(ChildProfile, child_profile_id)
    if child_profile is None or child_profile.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child profile not found")
    return child_profile


def validate_child_profile_ownership(session: Session, *, user_id: int, child_profile_id: int | None) -> ChildProfile | None:
    if child_profile_id is None:
        return None
    return get_child_profile_for_user(session, user_id=user_id, child_profile_id=child_profile_id)


def get_or_create_child_reading_profile(session: Session, *, child_profile_id: int) -> ChildReadingProfile:
    profile = session.exec(
        select(ChildReadingProfile).where(ChildReadingProfile.child_profile_id == child_profile_id)
    ).first()
    if profile is None:
        profile = ChildReadingProfile(child_profile_id=child_profile_id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def create_child_profile(
    session: Session,
    *,
    user_id: int,
    display_name: str,
    birth_year: int | None,
    age_band: str,
    language: str,
    content_lane_key: str | None,
    is_active: bool,
) -> tuple[ChildProfile, ChildReadingProfile]:
    resolved_age_band = _validate_age_band(age_band)
    lane_key = resolve_child_content_lane(
        session,
        age_band=resolved_age_band,
        content_lane_key=content_lane_key,
    )
    child_profile = ChildProfile(
        user_id=user_id,
        display_name=display_name,
        birth_year=birth_year,
        age_band=resolved_age_band,
        language=validate_language_code(language),
        content_lane_key=lane_key,
        is_active=is_active,
    )
    session.add(child_profile)
    session.commit()
    session.refresh(child_profile)
    reading_profile = get_or_create_child_reading_profile(session, child_profile_id=child_profile.id)
    return child_profile, reading_profile


def update_child_profile(
    session: Session,
    *,
    child_profile: ChildProfile,
    display_name: str | None = None,
    birth_year: int | None = None,
    age_band: str | None = None,
    language: str | None = None,
    content_lane_key: str | None = None,
    is_active: bool | None = None,
) -> ChildProfile:
    resolved_age_band = _validate_age_band(age_band or child_profile.age_band)
    if display_name is not None:
        child_profile.display_name = display_name
    if birth_year is not None:
        child_profile.birth_year = birth_year
    child_profile.age_band = resolved_age_band
    if language is not None:
        child_profile.language = validate_language_code(language)
    lane_key = resolve_child_content_lane(
        session,
        age_band=resolved_age_band,
        content_lane_key=content_lane_key if content_lane_key is not None else child_profile.content_lane_key,
    )
    child_profile.content_lane_key = lane_key
    if is_active is not None:
        child_profile.is_active = is_active
    child_profile.updated_at = utc_now()
    session.add(child_profile)
    session.commit()
    session.refresh(child_profile)
    return child_profile


def deactivate_child_profile(session: Session, *, child_profile: ChildProfile) -> ChildProfile:
    child_profile.is_active = False
    child_profile.updated_at = utc_now()
    session.add(child_profile)
    session.commit()
    session.refresh(child_profile)
    return child_profile


def _story_length_label(session: Session, book: Book) -> str | None:
    story_draft = session.get(StoryDraft, book.story_draft_id)
    if story_draft is None:
        return None
    if story_draft.read_time_minutes <= 5:
        return "short"
    if story_draft.read_time_minutes <= 8:
        return "medium"
    return "long"


def _story_setting(session: Session, book: Book) -> str | None:
    story_draft = session.get(StoryDraft, book.story_draft_id)
    if story_draft is None or story_draft.story_idea_id is None:
        return None
    story_idea = session.get(StoryIdea, story_draft.story_idea_id)
    return story_idea.setting if story_idea is not None else None


def rebuild_child_reading_profile(session: Session, *, child_profile: ChildProfile) -> ChildReadingProfile:
    profile = get_or_create_child_reading_profile(session, child_profile_id=child_profile.id)
    feedback_rows = list(
        session.exec(
            select(UserStoryFeedback).where(UserStoryFeedback.child_profile_id == child_profile.id)
        ).all()
    )
    progress_rows = list(
        session.exec(
            select(ReadingProgress).where(ReadingProgress.child_profile_id == child_profile.id)
        ).all()
    )
    books_by_id: dict[int, Book] = {}
    preferred_lengths: list[str] = []
    preferred_settings: list[str] = []
    for feedback in feedback_rows:
        book = books_by_id.get(feedback.book_id)
        if book is None:
            book = session.get(Book, feedback.book_id)
            if book is not None:
                books_by_id[feedback.book_id] = book
        if book is not None:
            length_label = _story_length_label(session, book)
            setting_label = _story_setting(session, book)
            if length_label:
                preferred_lengths.append(length_label)
            if setting_label:
                preferred_settings.append(setting_label)

    profile.favorite_characters = _top_values([row.preferred_character or "" for row in feedback_rows])
    profile.preferred_tones = _top_values([row.preferred_tone or "" for row in feedback_rows])
    profile.preferred_styles = _top_values([row.preferred_style or "" for row in feedback_rows])
    profile.preferred_lengths = _top_values(preferred_lengths)
    profile.preferred_settings = _top_values(preferred_settings)
    profile.total_books_completed = max(
        sum(1 for row in feedback_rows if row.completed),
        sum(1 for row in progress_rows if row.completed),
    )
    profile.total_books_replayed = sum(1 for row in feedback_rows if row.replayed)
    profile.last_profile_refresh_at = utc_now()
    profile.updated_at = utc_now()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
