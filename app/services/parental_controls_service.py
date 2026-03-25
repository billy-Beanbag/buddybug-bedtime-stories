from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, ChildControlOverride, ChildProfile, NarrationVoice, ParentalControlSettings, User
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.content_lane_service import is_adventure_lane_key
from app.services.review_service import utc_now

SUPPORTED_PARENTAL_AGE_BANDS = {"3-7", "8-12"}
AGE_BAND_ORDER = {"3-7": 0, "8-12": 1}


@dataclass
class ResolvedParentalControls:
    user_id: int
    child_profile_id: int | None
    bedtime_mode_enabled: bool
    allow_audio_autoplay: bool
    allow_8_12_content: bool
    allow_premium_voice_content: bool
    hide_adventure_content_at_bedtime: bool
    max_allowed_age_band: str
    quiet_mode_enabled: bool


def _validate_age_band(age_band: str) -> str:
    if age_band not in SUPPORTED_PARENTAL_AGE_BANDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported parental controls age band")
    return age_band


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def get_or_create_parental_settings(session: Session, *, user_id: int) -> ParentalControlSettings:
    settings = session.exec(select(ParentalControlSettings).where(ParentalControlSettings.user_id == user_id)).first()
    if settings is None:
        settings = ParentalControlSettings(user_id=user_id)
        settings = _persist(session, settings)
    return settings


def update_parental_settings(
    session: Session,
    *,
    settings: ParentalControlSettings,
    bedtime_mode_default: bool | None = None,
    allow_audio_autoplay: bool | None = None,
    allow_8_12_content: bool | None = None,
    allow_premium_voice_content: bool | None = None,
    hide_adventure_content_at_bedtime: bool | None = None,
    max_allowed_age_band: str | None = None,
    quiet_mode_default: bool | None = None,
) -> ParentalControlSettings:
    if bedtime_mode_default is not None:
        settings.bedtime_mode_default = bedtime_mode_default
    if allow_audio_autoplay is not None:
        settings.allow_audio_autoplay = allow_audio_autoplay
    if allow_8_12_content is not None:
        settings.allow_8_12_content = allow_8_12_content
    if allow_premium_voice_content is not None:
        settings.allow_premium_voice_content = allow_premium_voice_content
    if hide_adventure_content_at_bedtime is not None:
        settings.hide_adventure_content_at_bedtime = hide_adventure_content_at_bedtime
    if max_allowed_age_band is not None:
        settings.max_allowed_age_band = _validate_age_band(max_allowed_age_band)
    if quiet_mode_default is not None:
        settings.quiet_mode_default = quiet_mode_default
    settings.updated_at = utc_now()
    return _persist(session, settings)


def get_child_override(session: Session, *, child_profile_id: int) -> ChildControlOverride | None:
    return session.exec(select(ChildControlOverride).where(ChildControlOverride.child_profile_id == child_profile_id)).first()


def get_or_create_child_override_placeholder(*, child_profile_id: int) -> ChildControlOverride:
    now = utc_now()
    return ChildControlOverride(id=0, child_profile_id=child_profile_id, created_at=now, updated_at=now)


def upsert_child_override(
    session: Session,
    *,
    child_profile_id: int,
    bedtime_mode_enabled: bool | None = None,
    allow_audio_autoplay: bool | None = None,
    allow_8_12_content: bool | None = None,
    allow_premium_voice_content: bool | None = None,
    quiet_mode_enabled: bool | None = None,
    max_allowed_age_band: str | None = None,
) -> ChildControlOverride:
    override = get_child_override(session, child_profile_id=child_profile_id)
    if override is None:
        override = ChildControlOverride(child_profile_id=child_profile_id)
    override.bedtime_mode_enabled = bedtime_mode_enabled
    override.allow_audio_autoplay = allow_audio_autoplay
    override.allow_8_12_content = allow_8_12_content
    override.allow_premium_voice_content = allow_premium_voice_content
    override.quiet_mode_enabled = quiet_mode_enabled
    override.max_allowed_age_band = _validate_age_band(max_allowed_age_band) if max_allowed_age_band is not None else None
    override.updated_at = utc_now()
    return _persist(session, override)


def resolve_parental_controls(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
) -> ResolvedParentalControls:
    settings = get_or_create_parental_settings(session, user_id=user.id)
    child_profile = validate_child_profile_ownership(session, user_id=user.id, child_profile_id=child_profile_id)
    override = get_child_override(session, child_profile_id=child_profile.id) if child_profile is not None else None
    return ResolvedParentalControls(
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        bedtime_mode_enabled=(
            override.bedtime_mode_enabled if override is not None and override.bedtime_mode_enabled is not None else settings.bedtime_mode_default
        ),
        allow_audio_autoplay=(
            override.allow_audio_autoplay if override is not None and override.allow_audio_autoplay is not None else settings.allow_audio_autoplay
        ),
        allow_8_12_content=(
            override.allow_8_12_content if override is not None and override.allow_8_12_content is not None else settings.allow_8_12_content
        ),
        allow_premium_voice_content=(
            override.allow_premium_voice_content
            if override is not None and override.allow_premium_voice_content is not None
            else settings.allow_premium_voice_content
        ),
        hide_adventure_content_at_bedtime=settings.hide_adventure_content_at_bedtime,
        max_allowed_age_band=(
            override.max_allowed_age_band if override is not None and override.max_allowed_age_band is not None else settings.max_allowed_age_band
        ),
        quiet_mode_enabled=(
            override.quiet_mode_enabled if override is not None and override.quiet_mode_enabled is not None else settings.quiet_mode_default
        ),
    )


def is_age_band_allowed(*, requested_age_band: str, controls: ResolvedParentalControls) -> bool:
    normalized_age_band = _validate_age_band(requested_age_band)
    if AGE_BAND_ORDER[normalized_age_band] > AGE_BAND_ORDER[controls.max_allowed_age_band]:
        return False
    if normalized_age_band == "8-12" and not controls.allow_8_12_content:
        return False
    return True


def is_book_allowed(book: Book, *, controls: ResolvedParentalControls) -> bool:
    if not is_age_band_allowed(requested_age_band=book.age_band, controls=controls):
        return False
    if controls.bedtime_mode_enabled and controls.hide_adventure_content_at_bedtime and is_adventure_lane_key(book.content_lane_key):
        return False
    return True


def filter_books_by_parental_controls(
    books: list[Book],
    *,
    controls: ResolvedParentalControls | None,
) -> list[Book]:
    if controls is None:
        return books
    return [book for book in books if is_book_allowed(book, controls=controls)]


def filter_recommendation_like_items_by_parental_controls(items: list, *, controls: ResolvedParentalControls | None) -> list:
    if controls is None:
        return items
    filtered = [
        item
        for item in items
        if is_age_band_allowed(requested_age_band=item.age_band, controls=controls)
        and not (
            controls.bedtime_mode_enabled
            and controls.hide_adventure_content_at_bedtime
            and is_adventure_lane_key(getattr(item, "content_lane_key", None))
        )
    ]
    if controls.bedtime_mode_enabled:
        filtered.sort(
            key=lambda item: (
                getattr(item, "content_lane_key", None) != "bedtime_3_7",
                -getattr(item, "score", 0),
            )
        )
    return filtered


def filter_voices_by_parental_controls(
    voices: list[NarrationVoice],
    *,
    controls: ResolvedParentalControls | None,
) -> list[NarrationVoice]:
    if controls is None:
        return voices
    if controls.allow_premium_voice_content:
        return voices
    return [voice for voice in voices if not voice.is_premium]


def should_enable_audio_autoplay(*, controls: ResolvedParentalControls | None) -> bool:
    return bool(controls is not None and controls.allow_audio_autoplay)


def should_enable_bedtime_mode(*, controls: ResolvedParentalControls | None) -> bool:
    return bool(controls is not None and controls.bedtime_mode_enabled)
