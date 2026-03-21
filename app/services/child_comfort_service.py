from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session, select

from app.models import ChildComfortProfile, ChildProfile
from app.services.child_profile_service import get_child_profile_for_user
from app.services.i18n_service import validate_language_code
from app.services.review_service import utc_now

SUPPORTED_AVOID_TAGS = {"spooky", "loud", "fast-paced", "sad", "conflict-heavy"}


@dataclass
class ChildComfortSignals:
    favorite_characters: set[str]
    favorite_moods: set[str]
    favorite_story_types: set[str]
    avoid_tags: set[str]
    preferred_language: str | None
    prefer_narration: bool
    prefer_shorter_stories: bool
    extra_calm_mode: bool


def parse_preference_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip().lower() for item in value.split(",") if item and item.strip()}


def _normalize_csv_for_storage(value: str | None, *, allowed_values: set[str] | None = None) -> str | None:
    if value is None:
        return None
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_item in value.split(","):
        item = raw_item.strip()
        lowered = item.lower()
        if not item or lowered in seen:
            continue
        if allowed_values is not None and lowered not in allowed_values:
            continue
        seen.add(lowered)
        normalized.append(lowered if allowed_values is not None else item)
    return ", ".join(normalized) if normalized else None


def _normalize_bedtime_notes(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned[:280] if cleaned else None


def get_child_comfort_profile(session: Session, *, child_profile_id: int) -> ChildComfortProfile | None:
    statement = select(ChildComfortProfile).where(ChildComfortProfile.child_profile_id == child_profile_id)
    return session.exec(statement).first()


def get_or_create_child_comfort_profile(
    session: Session,
    *,
    child_profile: ChildProfile,
) -> ChildComfortProfile:
    profile = get_child_comfort_profile(session, child_profile_id=child_profile.id)
    if profile is not None:
        return profile
    profile = ChildComfortProfile(
        child_profile_id=child_profile.id,
        preferred_language=child_profile.language,
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def update_child_comfort_profile(
    session: Session,
    *,
    profile: ChildComfortProfile,
    favorite_characters_csv: str | None = None,
    favorite_moods_csv: str | None = None,
    favorite_story_types_csv: str | None = None,
    avoid_tags_csv: str | None = None,
    preferred_language: str | None = None,
    prefer_narration: bool | None = None,
    prefer_shorter_stories: bool | None = None,
    extra_calm_mode: bool | None = None,
    bedtime_notes: str | None = None,
) -> ChildComfortProfile:
    profile.favorite_characters_csv = _normalize_csv_for_storage(favorite_characters_csv)
    profile.favorite_moods_csv = _normalize_csv_for_storage(favorite_moods_csv)
    profile.favorite_story_types_csv = _normalize_csv_for_storage(favorite_story_types_csv)
    profile.avoid_tags_csv = _normalize_csv_for_storage(avoid_tags_csv, allowed_values=SUPPORTED_AVOID_TAGS)
    profile.preferred_language = validate_language_code(preferred_language) if preferred_language else None
    if prefer_narration is not None:
        profile.prefer_narration = prefer_narration
    if prefer_shorter_stories is not None:
        profile.prefer_shorter_stories = prefer_shorter_stories
    if extra_calm_mode is not None:
        profile.extra_calm_mode = extra_calm_mode
    profile.bedtime_notes = _normalize_bedtime_notes(bedtime_notes)
    profile.updated_at = utc_now()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def get_child_comfort_signals(
    session: Session,
    *,
    child_profile_id: int,
) -> ChildComfortSignals:
    profile = get_child_comfort_profile(session, child_profile_id=child_profile_id)
    if profile is None:
        return ChildComfortSignals(
            favorite_characters=set(),
            favorite_moods=set(),
            favorite_story_types=set(),
            avoid_tags=set(),
            preferred_language=None,
            prefer_narration=False,
            prefer_shorter_stories=False,
            extra_calm_mode=False,
        )
    return ChildComfortSignals(
        favorite_characters=parse_preference_csv(profile.favorite_characters_csv),
        favorite_moods=parse_preference_csv(profile.favorite_moods_csv),
        favorite_story_types=parse_preference_csv(profile.favorite_story_types_csv),
        avoid_tags=parse_preference_csv(profile.avoid_tags_csv),
        preferred_language=profile.preferred_language,
        prefer_narration=profile.prefer_narration,
        prefer_shorter_stories=profile.prefer_shorter_stories,
        extra_calm_mode=profile.extra_calm_mode,
    )


def get_child_comfort_profile_for_user(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int,
) -> tuple[ChildProfile, ChildComfortProfile]:
    child_profile = get_child_profile_for_user(session, user_id=user_id, child_profile_id=child_profile_id)
    return child_profile, get_or_create_child_comfort_profile(session, child_profile=child_profile)
