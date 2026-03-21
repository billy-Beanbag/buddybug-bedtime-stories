from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, desc, select

from app.models import Book, BookNarration, NarrationSegment, NarrationVoice, User
from app.schemas.narration_schema import ReaderNarrationResponse
from app.services.i18n_service import get_localized_reader_pages, normalize_language
from app.services.parental_controls_service import filter_voices_by_parental_controls, resolve_parental_controls
from app.services.reader_service import get_published_book_or_404
from app.services.review_service import utc_now
from app.services.storage_service import build_mock_narration_segment_path, get_asset_url, save_bytes
from app.services.subscription_service import has_premium_access
from app.services.tts_adapter import LocalMockTTSAdapter, estimate_tts_duration_seconds


def list_available_voices(
    session: Session,
    language: str | None = None,
    *,
    user: User | None = None,
    child_profile_id: int | None = None,
) -> list[NarrationVoice]:
    statement = select(NarrationVoice).where(NarrationVoice.is_active.is_(True)).order_by(NarrationVoice.display_name)
    if language is not None:
        statement = statement.where(NarrationVoice.language == normalize_language(language))
    voices = list(session.exec(statement).all())
    controls = resolve_parental_controls(session, user=user, child_profile_id=child_profile_id) if user is not None else None
    return filter_voices_by_parental_controls(voices, controls=controls)


def get_voice_by_key(session: Session, key: str) -> NarrationVoice:
    voice = session.exec(select(NarrationVoice).where(NarrationVoice.key == key)).first()
    if voice is None or not voice.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Narration voice not found")
    return voice


def validate_voice_access(user: User | None, voice: NarrationVoice) -> NarrationVoice:
    if voice.is_premium and not has_premium_access(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Premium voice requires premium access")
    return voice


def _book_or_404(session: Session, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


def _existing_narration(
    session: Session,
    *,
    book_id: int,
    language: str,
    narration_voice_id: int,
) -> BookNarration | None:
    statement = (
        select(BookNarration)
        .where(
            BookNarration.book_id == book_id,
            BookNarration.language == language,
            BookNarration.narration_voice_id == narration_voice_id,
        )
        .order_by(desc(BookNarration.updated_at), desc(BookNarration.id))
    )
    return session.exec(statement).first()


def _list_segments(session: Session, *, narration_id: int) -> list[NarrationSegment]:
    return list(
        session.exec(
            select(NarrationSegment)
            .where(NarrationSegment.narration_id == narration_id)
            .order_by(NarrationSegment.page_number.asc())
        ).all()
    )


def _deactivate_matching_narrations(
    session: Session,
    *,
    book_id: int,
    language: str,
    narration_voice_id: int,
) -> None:
    matches = list(
        session.exec(
            select(BookNarration).where(
                BookNarration.book_id == book_id,
                BookNarration.language == language,
                BookNarration.narration_voice_id == narration_voice_id,
            )
        ).all()
    )
    for narration in matches:
        narration.is_active = False
        narration.updated_at = utc_now()
        session.add(narration)
    session.commit()


def generate_page_audio(
    *,
    adapter: LocalMockTTSAdapter,
    text: str,
    voice_key: str,
    language: str,
) -> tuple[bytes, int]:
    audio_bytes = adapter.generate_speech(text=text, voice_key=voice_key, language=language)
    return audio_bytes, estimate_tts_duration_seconds(text)


def create_narration_segments(
    session: Session,
    *,
    narration: BookNarration,
    voice: NarrationVoice,
    language: str,
    adapter: LocalMockTTSAdapter,
) -> list[NarrationSegment]:
    pages, _resolved_language = get_localized_reader_pages(
        session,
        narration.book_id,
        requested_language=language,
        current_user=None,
        apply_access_control=False,
    )
    segments: list[NarrationSegment] = []
    for page in pages:
        audio_bytes, duration_seconds = generate_page_audio(
            adapter=adapter,
            text=page.text_content,
            voice_key=voice.key,
            language=language,
        )
        asset_path = save_bytes(
            build_mock_narration_segment_path(
                book_id=narration.book_id,
                voice_key=voice.key,
                language=language,
                narration_id=narration.id,
                page_number=page.page_number,
            ),
            audio_bytes,
        )
        segment = NarrationSegment(
            narration_id=narration.id,
            page_number=page.page_number,
            audio_url=get_asset_url(asset_path),
            duration_seconds=duration_seconds,
        )
        session.add(segment)
        session.commit()
        session.refresh(segment)
        segments.append(segment)
    return segments


def generate_book_narration(
    session: Session,
    *,
    book_id: int,
    voice_key: str,
    language: str,
    replace_existing: bool = False,
    actor_user: User | None = None,
) -> tuple[BookNarration, list[NarrationSegment], NarrationVoice]:
    book = _book_or_404(session, book_id)
    if book.publication_status not in {"ready", "published"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book must be ready or published")
    voice = get_voice_by_key(session, voice_key)
    if actor_user is not None and not actor_user.is_admin:
        validate_voice_access(actor_user, voice)
    normalized_language = normalize_language(language)
    if voice.language != normalized_language:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voice language does not match request")

    existing = _existing_narration(
        session,
        book_id=book.id,
        language=normalized_language,
        narration_voice_id=voice.id,
    )
    if existing is not None and not replace_existing:
        return existing, _list_segments(session, narration_id=existing.id), voice

    _deactivate_matching_narrations(
        session,
        book_id=book.id,
        language=normalized_language,
        narration_voice_id=voice.id,
    )
    narration = BookNarration(
        book_id=book.id,
        language=normalized_language,
        narration_voice_id=voice.id,
        is_active=True,
    )
    session.add(narration)
    session.commit()
    session.refresh(narration)

    adapter = LocalMockTTSAdapter()
    segments = create_narration_segments(
        session,
        narration=narration,
        voice=voice,
        language=normalized_language,
        adapter=adapter,
    )
    narration.duration_seconds = sum(segment.duration_seconds or 0 for segment in segments) or None
    narration.updated_at = utc_now()
    session.add(narration)
    book.audio_available = True
    book.updated_at = utc_now()
    session.add(book)
    session.commit()
    session.refresh(narration)
    return narration, segments, voice


def _accessible_narration_candidates(
    session: Session,
    *,
    book_id: int,
    language: str,
    user: User | None,
    child_profile_id: int | None = None,
) -> list[tuple[BookNarration, NarrationVoice]]:
    narrations = list(
        session.exec(
            select(BookNarration)
            .where(BookNarration.book_id == book_id, BookNarration.language == language, BookNarration.is_active.is_(True))
            .order_by(desc(BookNarration.updated_at), desc(BookNarration.id))
        ).all()
    )
    controls = resolve_parental_controls(session, user=user, child_profile_id=child_profile_id) if user is not None else None
    candidates: list[tuple[BookNarration, NarrationVoice]] = []
    for narration in narrations:
        voice = session.get(NarrationVoice, narration.narration_voice_id)
        if voice is None or not voice.is_active:
            continue
        if voice.is_premium and not has_premium_access(user):
            continue
        if controls is not None and voice not in filter_voices_by_parental_controls([voice], controls=controls):
            continue
        candidates.append((narration, voice))
    return candidates


def fetch_reader_narration(
    session: Session,
    *,
    book_id: int,
    language: str | None,
    user: User | None = None,
    child_profile_id: int | None = None,
    voice_key: str | None = None,
) -> ReaderNarrationResponse:
    book = get_published_book_or_404(session, book_id)
    normalized_language = normalize_language(language or book.language)
    controls = resolve_parental_controls(session, user=user, child_profile_id=child_profile_id) if user is not None else None
    if voice_key is not None:
        voice = get_voice_by_key(session, voice_key)
        narration = session.exec(
            select(BookNarration)
            .where(
                BookNarration.book_id == book.id,
                BookNarration.language == normalized_language,
                BookNarration.narration_voice_id == voice.id,
                BookNarration.is_active.is_(True),
            )
            .order_by(desc(BookNarration.updated_at), desc(BookNarration.id))
        ).first()
        if narration is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested narration voice is unavailable")
        if controls is not None and voice not in filter_voices_by_parental_controls([voice], controls=controls):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This narration voice is disabled by parental controls")
        validate_voice_access(user, voice)
        return ReaderNarrationResponse(
            narration=narration,
            segments=_list_segments(session, narration_id=narration.id),
            voice=voice,
        )

    candidates = _accessible_narration_candidates(
        session,
        book_id=book.id,
        language=normalized_language,
        user=user,
        child_profile_id=child_profile_id,
    )
    if not candidates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Narration not found")

    selected_narration, selected_voice = candidates[0]
    segments = _list_segments(session, narration_id=selected_narration.id)
    return ReaderNarrationResponse(
        narration=selected_narration,
        segments=segments,
        voice=selected_voice,
    )


def list_book_narrations(
    session: Session,
    *,
    book_id: int,
) -> list[ReaderNarrationResponse]:
    narrations = list(
        session.exec(
            select(BookNarration)
            .where(BookNarration.book_id == book_id)
            .order_by(desc(BookNarration.updated_at), desc(BookNarration.id))
        ).all()
    )
    responses: list[ReaderNarrationResponse] = []
    for narration in narrations:
        voice = session.get(NarrationVoice, narration.narration_voice_id)
        if voice is None:
            continue
        responses.append(
            ReaderNarrationResponse(
                narration=narration,
                segments=_list_segments(session, narration_id=narration.id),
                voice=voice,
            )
        )
    return responses
