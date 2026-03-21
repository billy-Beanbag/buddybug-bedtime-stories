import math

from fastapi import HTTPException, status
from sqlmodel import Session, desc, select

from app.models import Book, BookAudio, BookNarration, BookPage, NarrationVoice
from app.services.review_service import utc_now
from app.services.storage_service import build_mock_audio_path, get_asset_url

ALLOWED_SCRIPT_SOURCES = {"approved_text", "assembled_book_text", "manual"}
ALLOWED_AUDIO_APPROVAL_STATUSES = {"generated", "approved", "rejected"}
ALLOWED_AUDIO_PROVIDERS = {"mock", "manual_upload", "future_tts_provider"}


def get_voice_or_404(session: Session, voice_id: int) -> NarrationVoice:
    voice = session.get(NarrationVoice, voice_id)
    if voice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Narration voice not found")
    return voice


def get_book_audio_or_404(session: Session, audio_id: int) -> BookAudio:
    audio = session.get(BookAudio, audio_id)
    if audio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book audio not found")
    return audio


def get_book_or_404(session: Session, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


def validate_script_source(script_source: str) -> str:
    if script_source not in ALLOWED_SCRIPT_SOURCES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid script source")
    return script_source


def validate_audio_approval_status(approval_status: str) -> str:
    if approval_status not in ALLOWED_AUDIO_APPROVAL_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio approval status")
    return approval_status


def validate_audio_provider(provider: str) -> str:
    if provider not in ALLOWED_AUDIO_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio provider")
    return provider


def persist_book_audio(session: Session, audio: BookAudio) -> BookAudio:
    session.add(audio)
    session.commit()
    session.refresh(audio)
    return audio


def list_available_voices(
    session: Session,
    *,
    language: str | None,
    is_active: bool | None,
) -> list[NarrationVoice]:
    statement = select(NarrationVoice).order_by(NarrationVoice.display_name)
    if language:
        statement = statement.where(NarrationVoice.language == language)
    if is_active is not None:
        statement = statement.where(NarrationVoice.is_active == is_active)
    return list(session.exec(statement).all())


def get_book_narration_script(session: Session, *, book: Book, script_source: str) -> str:
    validate_script_source(script_source)

    if script_source == "assembled_book_text":
        pages = list(
            session.exec(
                select(BookPage)
                .where(BookPage.book_id == book.id, BookPage.page_number > 0)
                .order_by(BookPage.page_number)
            ).all()
        )
        text_parts = [page.text_content.strip() for page in pages if page.text_content.strip()]
        if text_parts:
            return "\n\n".join(text_parts)

    if script_source == "approved_text":
        from app.models import StoryDraft

        story_draft = session.get(StoryDraft, book.story_draft_id)
        if story_draft and (story_draft.approved_text or story_draft.full_text):
            return (story_draft.approved_text or story_draft.full_text).strip()

    if script_source == "manual":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual script source requires providing script_text directly",
        )

    from app.models import StoryDraft

    story_draft = session.get(StoryDraft, book.story_draft_id)
    if story_draft and (story_draft.approved_text or story_draft.full_text):
        return (story_draft.approved_text or story_draft.full_text).strip()

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No narration script is available for this book",
    )


def estimate_duration_seconds(script_text: str) -> int:
    word_count = len(script_text.split())
    words_per_minute = 140
    return max(10, math.ceil((word_count / words_per_minute) * 60))


def determine_next_version_number(session: Session, *, book_id: int, voice_id: int) -> int:
    statement = (
        select(BookAudio)
        .where(BookAudio.book_id == book_id, BookAudio.voice_id == voice_id)
        .order_by(desc(BookAudio.version_number), desc(BookAudio.created_at))
    )
    latest = session.exec(statement).first()
    return 1 if latest is None else latest.version_number + 1


def refresh_book_audio_available(session: Session, *, book: Book) -> Book:
    approved_exists = session.exec(
        select(BookAudio).where(BookAudio.book_id == book.id, BookAudio.approval_status == "approved")
    ).first()
    narration_exists = session.exec(
        select(BookNarration).where(BookNarration.book_id == book.id, BookNarration.is_active.is_(True))
    ).first()
    book.audio_available = approved_exists is not None or narration_exists is not None
    book.updated_at = utc_now()
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def activate_book_audio(session: Session, *, audio: BookAudio) -> BookAudio:
    statement = select(BookAudio).where(BookAudio.book_id == audio.book_id, BookAudio.voice_id == audio.voice_id)
    siblings = list(session.exec(statement).all())
    for sibling in siblings:
        sibling.is_active = sibling.id == audio.id
        sibling.updated_at = utc_now()
        session.add(sibling)
    session.commit()
    session.refresh(audio)
    return audio


def generate_book_audio(
    session: Session,
    *,
    book_id: int,
    voice_id: int,
    script_source: str,
    generation_notes: str | None,
    replace_active_for_voice: bool,
) -> BookAudio:
    book = get_book_or_404(session, book_id)
    if book.publication_status not in {"ready", "published"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book must be ready or published before generating audio",
        )

    voice = get_voice_or_404(session, voice_id)
    if not voice.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Narration voice is inactive")

    script_text = get_book_narration_script(session, book=book, script_source=script_source)
    version_number = determine_next_version_number(session, book_id=book.id, voice_id=voice.id)
    audio_url = get_asset_url(
        build_mock_audio_path(
            book_id=book.id,
            voice_key=voice.key,
            version_number=version_number,
        )
    )

    audio = BookAudio(
        book_id=book.id,
        voice_id=voice.id,
        script_source=script_source,
        script_text=script_text,
        audio_url=audio_url,
        duration_seconds=estimate_duration_seconds(script_text),
        provider="mock",
        version_number=version_number,
        approval_status="generated",
        is_active=False,
        generation_notes=generation_notes,
    )
    session.add(audio)
    session.commit()
    session.refresh(audio)

    if replace_active_for_voice:
        activate_book_audio(session, audio=audio)
    refresh_book_audio_available(session, book=book)
    return audio


def approve_book_audio(
    session: Session,
    *,
    audio: BookAudio,
    generation_notes: str | None,
    make_active: bool,
) -> BookAudio:
    audio.approval_status = "approved"
    if generation_notes is not None:
        audio.generation_notes = generation_notes
    audio.updated_at = utc_now()
    session.add(audio)
    session.commit()
    session.refresh(audio)

    if make_active:
        audio = activate_book_audio(session, audio=audio)

    book = get_book_or_404(session, audio.book_id)
    refresh_book_audio_available(session, book=book)
    return audio


def reject_book_audio(
    session: Session,
    *,
    audio: BookAudio,
    generation_notes: str | None,
) -> BookAudio:
    audio.approval_status = "rejected"
    audio.is_active = False
    if generation_notes is not None:
        audio.generation_notes = generation_notes
    audio.updated_at = utc_now()
    session.add(audio)
    session.commit()
    session.refresh(audio)

    book = get_book_or_404(session, audio.book_id)
    refresh_book_audio_available(session, book=book)
    return audio
