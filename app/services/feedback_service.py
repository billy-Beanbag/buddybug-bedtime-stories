from collections import Counter

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, ChildProfile, ChildReadingProfile, StoryDraft, StoryIdea, UserStoryFeedback, UserStoryProfile
from app.services.book_builder import get_book_or_404
from app.services.child_profile_service import get_child_profile_for_user, rebuild_child_reading_profile
from app.services.review_service import utc_now


def _validate_rating(rating: int | None) -> None:
    if rating is not None and not 1 <= rating <= 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")


def _top_values(values: list[str], limit: int = 3) -> str | None:
    cleaned = [value.strip() for value in values if value and value.strip()]
    if not cleaned:
        return None
    counter = Counter(cleaned)
    return ", ".join(item for item, _count in counter.most_common(limit))


def _get_story_length_label(session: Session, book: Book) -> str | None:
    story_draft = session.get(StoryDraft, book.story_draft_id)
    if story_draft is None:
        return None
    if story_draft.read_time_minutes <= 5:
        return "short"
    if story_draft.read_time_minutes <= 8:
        return "medium"
    return "long"


def _get_story_setting(session: Session, book: Book) -> str | None:
    story_draft = session.get(StoryDraft, book.story_draft_id)
    if story_draft is None or story_draft.story_idea_id is None:
        return None
    story_idea = session.get(StoryIdea, story_draft.story_idea_id)
    return story_idea.setting if story_idea is not None else None


def get_feedback_for_user_and_book(
    session: Session,
    *,
    user_id: int,
    book_id: int,
    child_profile_id: int | None = None,
) -> UserStoryFeedback | None:
    statement = select(UserStoryFeedback).where(
        UserStoryFeedback.user_id == user_id,
        UserStoryFeedback.book_id == book_id,
    )
    if child_profile_id is None:
        statement = statement.where(UserStoryFeedback.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(UserStoryFeedback.child_profile_id == child_profile_id)
    return session.exec(statement).first()


def list_feedback_for_user(
    session: Session,
    *,
    user_id: int,
    liked: bool | None = None,
    completed: bool | None = None,
    replayed: bool | None = None,
    child_profile_id: int | None = None,
    limit: int = 100,
) -> list[UserStoryFeedback]:
    statement = (
        select(UserStoryFeedback)
        .where(UserStoryFeedback.user_id == user_id)
        .order_by(UserStoryFeedback.updated_at.desc())
        .limit(limit)
    )
    if child_profile_id is None:
        statement = statement.where(UserStoryFeedback.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(UserStoryFeedback.child_profile_id == child_profile_id)
    if liked is not None:
        statement = statement.where(UserStoryFeedback.liked == liked)
    if completed is not None:
        statement = statement.where(UserStoryFeedback.completed == completed)
    if replayed is not None:
        statement = statement.where(UserStoryFeedback.replayed == replayed)
    return list(session.exec(statement).all())


def _ensure_feedback_book_allowed(session: Session, book_id: int) -> Book:
    book = get_book_or_404(session, book_id)
    if not book.published or book.publication_status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be left on published books",
        )
    return book


def _get_or_create_profile(session: Session, user_id: int) -> UserStoryProfile:
    statement = select(UserStoryProfile).where(UserStoryProfile.user_id == user_id)
    profile = session.exec(statement).first()
    if profile is None:
        profile = UserStoryProfile(user_id=user_id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def rebuild_user_story_profile(session: Session, *, user_id: int) -> UserStoryProfile:
    profile = _get_or_create_profile(session, user_id)
    feedback_rows = list(
        session.exec(select(UserStoryFeedback).where(UserStoryFeedback.user_id == user_id)).all()
    )

    books_by_id: dict[int, Book] = {}
    preferred_lengths: list[str] = []
    preferred_settings: list[str] = []
    for feedback in feedback_rows:
        book = books_by_id.get(feedback.book_id)
        if book is None:
            try:
                book = get_book_or_404(session, feedback.book_id)
            except HTTPException:
                book = None
            if book is not None:
                books_by_id[feedback.book_id] = book
        if book is not None:
            length_label = _get_story_length_label(session, book)
            setting_label = _get_story_setting(session, book)
            if length_label is not None:
                preferred_lengths.append(length_label)
            if setting_label is not None:
                preferred_settings.append(setting_label)

    profile.favorite_characters = _top_values([row.preferred_character or "" for row in feedback_rows])
    profile.preferred_tones = _top_values([row.preferred_tone or "" for row in feedback_rows])
    profile.preferred_styles = _top_values([row.preferred_style or "" for row in feedback_rows])
    profile.preferred_lengths = _top_values(preferred_lengths)
    profile.preferred_settings = _top_values(preferred_settings)
    profile.total_books_rated = sum(1 for row in feedback_rows if row.rating is not None)
    profile.total_books_completed = sum(1 for row in feedback_rows if row.completed)
    profile.total_books_replayed = sum(1 for row in feedback_rows if row.replayed)
    profile.last_profile_refresh_at = utc_now()
    profile.updated_at = utc_now()

    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def create_or_update_feedback(
    session: Session,
    *,
    user_id: int,
    book_id: int,
    child_profile_id: int | None = None,
    liked: bool | None,
    rating: int | None,
    completed: bool,
    replayed: bool,
    preferred_character: str | None,
    preferred_style: str | None,
    preferred_tone: str | None,
    feedback_notes: str | None,
) -> tuple[UserStoryFeedback, UserStoryProfile]:
    _validate_rating(rating)
    _ensure_feedback_book_allowed(session, book_id)
    child_profile = (
        get_child_profile_for_user(session, user_id=user_id, child_profile_id=child_profile_id)
        if child_profile_id is not None
        else None
    )

    feedback = get_feedback_for_user_and_book(
        session,
        user_id=user_id,
        book_id=book_id,
        child_profile_id=child_profile_id,
    )
    now = utc_now()
    if feedback is None:
        feedback = UserStoryFeedback(
            user_id=user_id,
            book_id=book_id,
            child_profile_id=child_profile.id if child_profile is not None else None,
            liked=liked,
            rating=rating,
            completed=completed,
            replayed=replayed,
            preferred_character=preferred_character,
            preferred_style=preferred_style,
            preferred_tone=preferred_tone,
            feedback_notes=feedback_notes,
        )
    else:
        feedback.liked = liked
        feedback.rating = rating
        feedback.completed = completed
        feedback.replayed = replayed
        feedback.preferred_character = preferred_character
        feedback.preferred_style = preferred_style
        feedback.preferred_tone = preferred_tone
        feedback.feedback_notes = feedback_notes
        feedback.updated_at = now

    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    profile = rebuild_user_story_profile(session, user_id=user_id)
    if child_profile is not None:
        rebuild_child_reading_profile(session, child_profile=child_profile)
    return feedback, profile


def update_feedback(
    session: Session,
    *,
    feedback: UserStoryFeedback,
    liked: bool | None = None,
    rating: int | None = None,
    completed: bool | None = None,
    replayed: bool | None = None,
    preferred_character: str | None = None,
    preferred_style: str | None = None,
    preferred_tone: str | None = None,
    feedback_notes: str | None = None,
) -> tuple[UserStoryFeedback, UserStoryProfile]:
    if rating is not None:
        _validate_rating(rating)
        feedback.rating = rating
    if liked is not None:
        feedback.liked = liked
    if completed is not None:
        feedback.completed = completed
    if replayed is not None:
        feedback.replayed = replayed
    if preferred_character is not None:
        feedback.preferred_character = preferred_character
    if preferred_style is not None:
        feedback.preferred_style = preferred_style
    if preferred_tone is not None:
        feedback.preferred_tone = preferred_tone
    if feedback_notes is not None:
        feedback.feedback_notes = feedback_notes

    feedback.updated_at = utc_now()
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    profile = rebuild_user_story_profile(session, user_id=feedback.user_id)
    if feedback.child_profile_id is not None:
        child_profile = session.get(ChildProfile, feedback.child_profile_id)
        if child_profile is not None:
            rebuild_child_reading_profile(session, child_profile=child_profile)
    return feedback, profile
