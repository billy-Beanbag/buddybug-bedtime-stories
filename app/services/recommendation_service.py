from __future__ import annotations

from dataclasses import dataclass
import re

from sqlmodel import Session, select

from app.models import (
    Book,
    ChildProfile,
    ChildReadingProfile,
    StoryDraft,
    StoryIdea,
    StoryPage,
    User,
    UserStoryFeedback,
    UserStoryProfile,
)
from app.schemas.recommendation_schema import RecommendedBookScore
from app.services.child_comfort_service import ChildComfortSignals, get_child_comfort_signals
from app.services.child_profile_service import get_child_profile_for_user, get_or_create_child_reading_profile
from app.services.feedback_service import rebuild_user_story_profile
from app.services.i18n_service import get_book_translation, normalize_language
from app.services.parental_controls_service import filter_recommendation_like_items_by_parental_controls, resolve_parental_controls


def _split_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip().lower() for item in value.split(",") if item and item.strip()}


def _phrase_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    normalized = value.strip().lower()
    tokens = {normalized}
    tokens.update(_split_tokens(normalized))
    return {token for token in tokens if token}


def _lane_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {
        token
        for token in re.split(r"[_\-\s]+", value.strip().lower())
        if token and token not in {"3", "7", "8", "12", "story", "stories"}
    }


def _metadata_story_types(metadata: BookRecommendationMetadata) -> set[str]:
    tokens = set(metadata.styles)
    tokens.update(metadata.tones)
    tokens.update(_lane_tokens(metadata.book.content_lane_key))
    if metadata.book.content_lane_key == "bedtime_3_7":
        tokens.update({"bedtime", "calm"})
    return tokens


def _metadata_avoid_markers(metadata: BookRecommendationMetadata) -> set[str]:
    markers = set(metadata.tones)
    markers.update(metadata.styles)
    markers.update(metadata.settings)
    markers.update(_lane_tokens(metadata.book.content_lane_key))
    return markers


def _avoid_penalty(metadata: BookRecommendationMetadata, avoid_tags: set[str]) -> float:
    if not avoid_tags:
        return 0.0
    penalty = 0.0
    markers = _metadata_avoid_markers(metadata)
    avoid_map = {
        "spooky": {"spooky", "scary", "monster", "dark"},
        "loud": {"loud", "noisy", "wild"},
        "fast-paced": {"fast", "adventure", "race", "chase", "energetic"},
        "sad": {"sad", "lonely", "loss", "gloomy"},
        "conflict-heavy": {"battle", "fight", "conflict", "argument", "adventure"},
    }
    for avoid_tag in avoid_tags:
        if markers.intersection(avoid_map.get(avoid_tag, {avoid_tag})):
            penalty += 3.5
    return penalty


def _story_length_label(read_time_minutes: int | None) -> str | None:
    if read_time_minutes is None:
        return None
    if read_time_minutes <= 5:
        return "short"
    if read_time_minutes <= 8:
        return "medium"
    return "long"


def _calm_mode_tags(metadata: BookRecommendationMetadata) -> set[str]:
    return metadata.tones.union(metadata.styles).intersection({"calm", "gentle", "bedtime", "sleepy", "soothing"})


def _playful_mode_tags(metadata: BookRecommendationMetadata) -> set[str]:
    return metadata.tones.union(metadata.styles).intersection({"playful", "cheeky", "mischief", "mischievous", "fun"})


@dataclass
class PopularityStats:
    feedback_count: int = 0
    average_rating: float = 0.0
    like_count: int = 0
    replay_count: int = 0
    completion_count: int = 0


@dataclass
class BookRecommendationMetadata:
    book: Book
    story_draft: StoryDraft | None
    story_idea: StoryIdea | None
    characters: set[str]
    tones: set[str]
    styles: set[str]
    settings: set[str]
    length_label: str | None
    popularity: PopularityStats


def _list_recommendable_books(session: Session, *, age_band: str | None = None) -> list[Book]:
    statement = (
        select(Book)
        .where(Book.published.is_(True), Book.publication_status == "published")
        .order_by(Book.updated_at.desc())
    )
    if age_band:
        statement = statement.where(Book.age_band == age_band)
    return list(session.exec(statement).all())


def _build_story_lookup(session: Session, books: list[Book]) -> tuple[dict[int, StoryDraft], dict[int, StoryIdea], dict[int, list[StoryPage]]]:
    draft_ids = [book.story_draft_id for book in books]
    if not draft_ids:
        return {}, {}, {}
    drafts = {
        draft.id: draft
        for draft in session.exec(select(StoryDraft).where(StoryDraft.id.in_(draft_ids))).all()
    }
    idea_ids = [draft.story_idea_id for draft in drafts.values() if draft.story_idea_id is not None]
    ideas = (
        {
            idea.id: idea
            for idea in session.exec(select(StoryIdea).where(StoryIdea.id.in_(idea_ids))).all()
        }
        if idea_ids
        else {}
    )
    pages_by_draft: dict[int, list[StoryPage]] = {draft_id: [] for draft_id in draft_ids}
    pages = list(session.exec(select(StoryPage).where(StoryPage.story_draft_id.in_(draft_ids))).all()) if draft_ids else []
    for page in pages:
        pages_by_draft.setdefault(page.story_draft_id, []).append(page)
    return drafts, ideas, pages_by_draft


def _build_popularity_map(session: Session) -> dict[int, PopularityStats]:
    stats_by_book: dict[int, PopularityStats] = {}
    feedback_rows = list(session.exec(select(UserStoryFeedback)).all())
    ratings_by_book: dict[int, list[int]] = {}
    for row in feedback_rows:
        stats = stats_by_book.setdefault(row.book_id, PopularityStats())
        stats.feedback_count += 1
        if row.liked:
            stats.like_count += 1
        if row.replayed:
            stats.replay_count += 1
        if row.completed:
            stats.completion_count += 1
        if row.rating is not None:
            ratings_by_book.setdefault(row.book_id, []).append(row.rating)
    for book_id, ratings in ratings_by_book.items():
        stats_by_book.setdefault(book_id, PopularityStats()).average_rating = round(sum(ratings) / len(ratings), 2)
    return stats_by_book


def _infer_styles_for_book(session: Session, book_id: int) -> set[str]:
    feedback_rows = list(session.exec(select(UserStoryFeedback).where(UserStoryFeedback.book_id == book_id)).all())
    styles: set[str] = set()
    for row in feedback_rows:
        styles.update(_phrase_tokens(row.preferred_style))
    return styles


def _build_book_metadata_map(session: Session, books: list[Book]) -> dict[int, BookRecommendationMetadata]:
    drafts, ideas, pages_by_draft = _build_story_lookup(session, books)
    popularity_map = _build_popularity_map(session)
    metadata_map: dict[int, BookRecommendationMetadata] = {}
    for book in books:
        draft = drafts.get(book.story_draft_id)
        idea = ideas.get(draft.story_idea_id) if draft is not None and draft.story_idea_id is not None else None
        pages = pages_by_draft.get(book.story_draft_id, [])
        characters = set()
        tones = set()
        settings = set()
        if idea is not None:
            characters.update(_split_tokens(idea.main_characters))
            characters.update(_split_tokens(idea.supporting_characters))
            tones.update(_phrase_tokens(idea.tone))
            settings.update(_phrase_tokens(idea.setting))
        for page in pages:
            characters.update(_split_tokens(page.characters_present))
            tones.update(_phrase_tokens(page.mood))
            settings.update(_phrase_tokens(page.location))
        styles = _infer_styles_for_book(session, book.id)
        metadata_map[book.id] = BookRecommendationMetadata(
            book=book,
            story_draft=draft,
            story_idea=idea,
            characters=characters,
            tones=tones,
            styles=styles,
            settings=settings,
            length_label=_story_length_label(draft.read_time_minutes if draft is not None else None),
            popularity=popularity_map.get(book.id, PopularityStats()),
        )
    return metadata_map


def _get_or_create_profile(session: Session, user_id: int) -> UserStoryProfile:
    profile = session.exec(select(UserStoryProfile).where(UserStoryProfile.user_id == user_id)).first()
    if profile is None:
        profile = rebuild_user_story_profile(session, user_id=user_id)
    return profile


def _feedback_map_for_user(
    session: Session,
    user_id: int,
    *,
    child_profile_id: int | None = None,
) -> dict[int, UserStoryFeedback]:
    statement = select(UserStoryFeedback).where(UserStoryFeedback.user_id == user_id)
    if child_profile_id is None:
        statement = statement.where(UserStoryFeedback.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(UserStoryFeedback.child_profile_id == child_profile_id)
    return {feedback.book_id: feedback for feedback in session.exec(statement).all()}


def _localized_title(session: Session, book: Book, language: str | None) -> str:
    normalized_language = normalize_language(language)
    translation = get_book_translation(session, book_id=book.id, language=normalized_language)
    if translation is not None:
        return translation.title
    return book.title


def _unique_reasons(reasons: list[str], limit: int = 4) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason not in seen:
            ordered.append(reason)
            seen.add(reason)
        if len(ordered) >= limit:
            break
    return ordered


def score_book_for_user(
    session: Session,
    *,
    preferred_language: str,
    book: Book,
    metadata: BookRecommendationMetadata,
    profile: UserStoryProfile | ChildReadingProfile | None,
    feedback: UserStoryFeedback | None,
    requested_language: str | None = None,
    comfort_signals: ChildComfortSignals | None = None,
    bedtime_mode_enabled: bool = False,
) -> RecommendedBookScore:
    score = 0.0
    reasons: list[str] = []
    effective_language = normalize_language(
        requested_language or (comfort_signals.preferred_language if comfort_signals is not None else None) or preferred_language
    )

    if book.language == effective_language:
        score += 3
        reasons.append("Matches your preferred language")

    preferred_characters = _split_tokens(profile.favorite_characters) if profile is not None else set()
    if preferred_characters and metadata.characters.intersection(preferred_characters):
        score += 3
        reasons.append("Features characters you enjoy")

    preferred_tones = _phrase_tokens(profile.preferred_tones) if profile is not None else set()
    if preferred_tones and metadata.tones.intersection(preferred_tones):
        score += 2
        reasons.append("Matches the tone you usually enjoy")

    preferred_styles = _phrase_tokens(profile.preferred_styles) if profile is not None else set()
    if preferred_styles and metadata.styles.intersection(preferred_styles):
        score += 1
        reasons.append("Matches the story style you prefer")

    preferred_settings = _phrase_tokens(profile.preferred_settings) if profile is not None else set()
    if preferred_settings and metadata.settings.intersection(preferred_settings):
        score += 1
        reasons.append("Set in a bedtime world you enjoy")

    preferred_lengths = _split_tokens(profile.preferred_lengths) if profile is not None else set()
    if metadata.length_label is not None and metadata.length_label in preferred_lengths:
        score += 1
        reasons.append("Fits your usual story length")

    if comfort_signals is not None:
        if comfort_signals.favorite_characters and metadata.characters.intersection(comfort_signals.favorite_characters):
            score += 2.5
            reasons.append("Features favorite characters")
        if comfort_signals.favorite_moods and metadata.tones.intersection(comfort_signals.favorite_moods):
            score += 2
            reasons.append("Matches a mood they usually enjoy")
        if comfort_signals.favorite_story_types and _metadata_story_types(metadata).intersection(comfort_signals.favorite_story_types):
            score += 1.5
            reasons.append("Fits their favorite story style")
        if comfort_signals.prefer_narration and book.audio_available:
            score += 1.5
            reasons.append("Ready for narration")
        if comfort_signals.prefer_shorter_stories and metadata.length_label == "short":
            score += 2
            reasons.append("A shorter, gentler read")
        if comfort_signals.extra_calm_mode:
            if metadata.book.content_lane_key == "bedtime_3_7":
                score += 2.5
                reasons.append("A calmer bedtime-friendly pick")
            elif _calm_mode_tags(metadata):
                score += 1.5
                reasons.append("Leans extra calm")
        score -= _avoid_penalty(metadata, comfort_signals.avoid_tags)

    if bedtime_mode_enabled:
        if _calm_mode_tags(metadata):
            score += 2.25
            reasons.append("Fits bedtime mode")
        if _playful_mode_tags(metadata):
            score -= 0.5
    elif _playful_mode_tags(metadata):
        score += 1.0
        reasons.append("Adds playful energy")

    if metadata.popularity.average_rating >= 4 and metadata.popularity.feedback_count >= 1:
        score += 1
        reasons.append("Popular with readers")
    if metadata.popularity.replay_count > 0:
        score += 1
        reasons.append("Frequently replayed by families")

    if feedback is not None:
        if feedback.liked is False:
            score -= 3
        elif feedback.liked is True:
            score += 0.5
            reasons.append("Because you liked a similar Buddybug story")
        if feedback.completed and not feedback.replayed:
            score -= 0.5
        if feedback.replayed:
            score += 1
            reasons.append("You replay stories like this")

    return RecommendedBookScore(
        book_id=book.id,
        title=_localized_title(session, book, effective_language),
        cover_image_url=book.cover_image_url,
        age_band=book.age_band,
        content_lane_key=book.content_lane_key,
        is_classic=book.is_classic,
        language=book.language,
        published=book.published,
        publication_status=book.publication_status,
        score=round(score, 2),
        reasons=_unique_reasons(reasons) or ["Published bedtime story"],
    )


def get_fallback_recommendations(
    session: Session,
    *,
    language: str | None,
    age_band: str | None = None,
    limit: int = 20,
) -> list[RecommendedBookScore]:
    books = _list_recommendable_books(session, age_band=age_band)
    metadata_map = _build_book_metadata_map(session, books)
    normalized_language = normalize_language(language)
    scored: list[RecommendedBookScore] = []
    for book in books:
        metadata = metadata_map[book.id]
        score = 0.0
        reasons: list[str] = []
        if book.language == normalized_language:
            score += 3
            reasons.append("Available in your preferred language")
        if metadata.popularity.average_rating >= 4 and metadata.popularity.feedback_count >= 1:
            score += 1.5
            reasons.append("Popular with readers")
        if metadata.popularity.replay_count > 0:
            score += 1
            reasons.append("Frequently replayed by families")
        score += min(metadata.popularity.feedback_count * 0.1, 1.0)
        scored.append(
            RecommendedBookScore(
                book_id=book.id,
                title=_localized_title(session, book, normalized_language),
                cover_image_url=book.cover_image_url,
                age_band=book.age_band,
                content_lane_key=book.content_lane_key,
                is_classic=book.is_classic,
                language=book.language,
                published=book.published,
                publication_status=book.publication_status,
                score=round(score, 2),
                reasons=_unique_reasons(reasons) or ["Published bedtime story"],
            )
        )
    scored.sort(key=lambda item: (-item.score, item.title.lower(), -item.book_id))
    return scored[:limit]


def get_personalized_recommendations_for_user(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
    age_band: str | None = None,
    limit: int = 20,
) -> tuple[list[RecommendedBookScore], int]:
    child_profile: ChildProfile | None = None
    effective_age_band = age_band
    effective_language = user.language
    profile: UserStoryProfile | ChildReadingProfile | None
    comfort_signals: ChildComfortSignals | None = None
    controls = resolve_parental_controls(session, user=user, child_profile_id=child_profile_id)
    if child_profile_id is not None:
        child_profile = get_child_profile_for_user(session, user_id=user.id, child_profile_id=child_profile_id)
        effective_age_band = child_profile.age_band
        effective_language = child_profile.language
        profile = get_or_create_child_reading_profile(session, child_profile_id=child_profile.id)
        comfort_signals = get_child_comfort_signals(session, child_profile_id=child_profile.id)
        if comfort_signals.preferred_language:
            effective_language = comfort_signals.preferred_language
    else:
        profile = _get_or_create_profile(session, user.id)

    books = _list_recommendable_books(session, age_band=effective_age_band)
    metadata_map = _build_book_metadata_map(session, books)
    feedback_map = _feedback_map_for_user(
        session,
        user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
    )
    scored = [
        score_book_for_user(
            session,
            preferred_language=effective_language,
            book=book,
            metadata=metadata_map[book.id],
            profile=profile,
            feedback=feedback_map.get(book.id),
            requested_language=effective_language,
            comfort_signals=comfort_signals,
            bedtime_mode_enabled=controls.bedtime_mode_enabled,
        )
        for book in books
    ]
    scored.sort(key=lambda item: (-item.score, item.title.lower(), -item.book_id))
    if not scored:
        return [], 0
    if all(item.score <= 0 for item in scored):
        fallback = get_fallback_recommendations(
            session,
            language=effective_language,
            age_band=effective_age_band,
            limit=limit,
        )
        return filter_recommendation_like_items_by_parental_controls(fallback, controls=controls)[:limit], len(books)
    return filter_recommendation_like_items_by_parental_controls(scored, controls=controls)[:limit], len(books)


def _similarity_score(
    source: BookRecommendationMetadata,
    candidate: BookRecommendationMetadata,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if source.book.language == candidate.book.language:
        score += 2
        reasons.append("Available in the same language")
    if source.characters.intersection(candidate.characters):
        score += 3
        reasons.append("Features similar characters")
    if source.tones.intersection(candidate.tones):
        score += 2
        reasons.append("Similar story tone")
    if source.settings.intersection(candidate.settings):
        score += 1
        reasons.append("Set in a similar bedtime world")
    if source.length_label and source.length_label == candidate.length_label:
        score += 1
        reasons.append("Similar story length")
    return score, reasons


def get_more_like_this(
    session: Session,
    *,
    book_id: int,
    user: User | None = None,
    child_profile_id: int | None = None,
    user_context: bool = True,
    limit: int = 10,
) -> list[RecommendedBookScore]:
    books = _list_recommendable_books(session)
    metadata_map = _build_book_metadata_map(session, books)
    source = metadata_map.get(book_id)
    if source is None:
        return []

    child_profile: ChildProfile | None = None
    controls = resolve_parental_controls(session, user=user, child_profile_id=child_profile_id) if user is not None else None
    if user is not None and child_profile_id is not None:
        child_profile = get_child_profile_for_user(session, user_id=user.id, child_profile_id=child_profile_id)
    profile = (
        get_or_create_child_reading_profile(session, child_profile_id=child_profile.id)
        if child_profile is not None
        else (_get_or_create_profile(session, user.id) if user is not None else None)
    )
    feedback_map = (
        _feedback_map_for_user(
            session,
            user.id,
            child_profile_id=child_profile.id if child_profile is not None else None,
        )
        if user is not None
        else {}
    )
    preferred_language = child_profile.language if child_profile is not None else (user.language if user is not None else None)
    comfort_signals = get_child_comfort_signals(session, child_profile_id=child_profile.id) if child_profile is not None else None
    if comfort_signals is not None and comfort_signals.preferred_language:
        preferred_language = comfort_signals.preferred_language
    scored: list[RecommendedBookScore] = []
    for book in books:
        if book.id == book_id:
            continue
        candidate = metadata_map[book.id]
        similarity_score, reasons = _similarity_score(source, candidate)
        final_score = similarity_score
        if user is not None and user_context:
            user_scored = score_book_for_user(
                session,
                preferred_language=preferred_language or book.language,
                book=book,
                metadata=candidate,
                profile=profile,
                feedback=feedback_map.get(book.id),
                requested_language=preferred_language or book.language,
                comfort_signals=comfort_signals,
                bedtime_mode_enabled=bool(controls is not None and controls.bedtime_mode_enabled),
            )
            final_score += max(user_scored.score, 0) * 0.5
            reasons.extend(user_scored.reasons)
        if candidate.popularity.average_rating >= 4 and candidate.popularity.feedback_count >= 1:
            final_score += 1
            reasons.append("Popular with readers")
        scored.append(
            RecommendedBookScore(
                book_id=book.id,
                title=_localized_title(session, book, preferred_language or book.language),
                cover_image_url=book.cover_image_url,
                age_band=book.age_band,
                content_lane_key=book.content_lane_key,
                is_classic=book.is_classic,
                language=book.language,
                published=book.published,
                publication_status=book.publication_status,
                score=round(final_score, 2),
                reasons=_unique_reasons(reasons) or ["Similar bedtime story"],
            )
        )
    scored.sort(key=lambda item: (-item.score, item.title.lower(), -item.book_id))
    return filter_recommendation_like_items_by_parental_controls(scored, controls=controls)[:limit]
