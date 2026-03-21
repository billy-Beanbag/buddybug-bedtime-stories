from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlmodel import Session, desc, select

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import BookAudio, NarrationVoice, User
from app.schemas.audio_schema import (
    BookAudioApprovalRequest,
    BookAudioCreate,
    BookAudioGenerateRequest,
    BookAudioGenerateResponse,
    BookAudioRead,
    BookAudioUpdate,
    NarrationVoiceCreate,
    NarrationVoiceRead,
    NarrationVoiceUpdate,
    ReaderAudioSummary,
)
from app.services.audit_service import create_audit_log
from app.services.audio_service import (
    activate_book_audio,
    approve_book_audio,
    generate_book_audio,
    get_book_audio_or_404,
    get_book_or_404,
    get_voice_or_404,
    list_available_voices,
    persist_book_audio,
    refresh_book_audio_available,
    reject_book_audio,
    validate_audio_approval_status,
    validate_audio_provider,
    validate_script_source,
)
from app.services.i18n_service import normalize_language, validate_language_code
from app.services.reader_service import get_published_book_or_404
from app.services.review_service import utc_now
from app.services.subscription_service import has_premium_access
from app.utils.dependencies import get_optional_current_user

router = APIRouter(prefix="/audio", tags=["audio"])


def _persist_voice(session: Session, voice: NarrationVoice) -> NarrationVoice:
    session.add(voice)
    session.commit()
    session.refresh(voice)
    return voice


def _voice_key_exists(session: Session, key: str, exclude_id: int | None = None) -> bool:
    statement = select(NarrationVoice).where(NarrationVoice.key == key)
    voice = session.exec(statement).first()
    return voice is not None and voice.id != exclude_id


def _sync_audio_after_write(session: Session, audio: BookAudio) -> BookAudio:
    book = get_book_or_404(session, audio.book_id)
    refresh_book_audio_available(session, book=book)
    return audio


@router.get("/voices", response_model=list[NarrationVoiceRead], summary="List narration voices")
def list_voices(
    language: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[NarrationVoice]:
    return list_available_voices(session, language=language, is_active=is_active)


@router.get("/voices/{voice_id}", response_model=NarrationVoiceRead, summary="Get one narration voice")
def get_voice(voice_id: int, session: Session = Depends(get_session)) -> NarrationVoice:
    return get_voice_or_404(session, voice_id)


@router.post("/voices", response_model=NarrationVoiceRead, status_code=status.HTTP_201_CREATED, summary="Create one narration voice")
def create_voice(payload: NarrationVoiceCreate, session: Session = Depends(get_session)) -> NarrationVoice:
    if _voice_key_exists(session, payload.key):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voice key already exists")
    voice = NarrationVoice.model_validate(payload.model_copy(update={"language": validate_language_code(payload.language)}))
    return _persist_voice(session, voice)


@router.patch("/voices/{voice_id}", response_model=NarrationVoiceRead, summary="Partially update one narration voice")
def update_voice(
    voice_id: int,
    payload: NarrationVoiceUpdate,
    session: Session = Depends(get_session),
) -> NarrationVoice:
    voice = get_voice_or_404(session, voice_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "key" in update_data and update_data["key"] is not None and _voice_key_exists(session, update_data["key"], exclude_id=voice.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voice key already exists")
    if "language" in update_data and update_data["language"] is not None:
        update_data["language"] = validate_language_code(update_data["language"])
    for field_name, value in update_data.items():
        setattr(voice, field_name, value)
    voice.updated_at = utc_now()
    return _persist_voice(session, voice)


@router.delete("/voices/{voice_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft delete one narration voice")
def delete_voice(voice_id: int, session: Session = Depends(get_session)) -> Response:
    voice = get_voice_or_404(session, voice_id)
    voice.is_active = False
    voice.updated_at = utc_now()
    _persist_voice(session, voice)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/books", response_model=list[BookAudioRead], summary="List book audio records")
def list_book_audio(
    book_id: int | None = Query(default=None),
    voice_id: int | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
) -> list[BookAudio]:
    statement = select(BookAudio).order_by(desc(BookAudio.created_at)).limit(limit)
    if book_id is not None:
        statement = statement.where(BookAudio.book_id == book_id)
    if voice_id is not None:
        statement = statement.where(BookAudio.voice_id == voice_id)
    if approval_status:
        validate_audio_approval_status(approval_status)
        statement = statement.where(BookAudio.approval_status == approval_status)
    if is_active is not None:
        statement = statement.where(BookAudio.is_active == is_active)
    return list(session.exec(statement).all())


@router.get("/books/by-book/{book_id}", response_model=list[BookAudioRead], summary="List all audio versions for one book")
def get_book_audio_by_book(book_id: int, session: Session = Depends(get_session)) -> list[BookAudio]:
    get_book_or_404(session, book_id)
    audios = list(session.exec(select(BookAudio).where(BookAudio.book_id == book_id)).all())
    audios.sort(key=lambda item: (item.voice_id, -item.version_number, -item.id))
    return audios


@router.get(
    "/books/by-book/{book_id}/reader",
    response_model=list[ReaderAudioSummary],
    summary="Get reader-friendly audio options for one book",
)
def get_reader_audio_options(
    book_id: int,
    language: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[ReaderAudioSummary]:
    book = get_published_book_or_404(session, book_id)
    if not has_premium_access(current_user):
        return []
    audios = list(session.exec(select(BookAudio).where(BookAudio.book_id == book_id)).all())
    if not audios:
        return []

    target_language = normalize_language(language) if language else (book.language or "en")
    approved = [audio for audio in audios if audio.approval_status == "approved"]
    selected = approved if approved else audios
    selected.sort(key=lambda item: (item.voice_id, -item.version_number, -item.id))

    summaries: list[ReaderAudioSummary] = []
    for audio in selected:
        voice = get_voice_or_404(session, audio.voice_id)
        if voice.language != target_language:
            continue
        summaries.append(
            ReaderAudioSummary(
                id=audio.id,
                book_id=audio.book_id,
                voice_id=audio.voice_id,
                voice_key=voice.key,
                voice_display_name=voice.display_name,
                language=voice.language,
                audio_url=audio.audio_url,
                duration_seconds=audio.duration_seconds,
                is_active=audio.is_active,
                approval_status=audio.approval_status,
            )
        )
    return summaries


@router.post(
    "/books/generate",
    response_model=BookAudioGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a mock narration record for a book",
)
def generate_audio(
    payload: BookAudioGenerateRequest,
    session: Session = Depends(get_session),
) -> BookAudioGenerateResponse:
    audio = generate_book_audio(
        session,
        book_id=payload.book_id,
        voice_id=payload.voice_id,
        script_source=payload.script_source,
        generation_notes=payload.generation_notes,
        replace_active_for_voice=payload.replace_active_for_voice,
    )
    return BookAudioGenerateResponse(audio=audio, book_id=audio.book_id, voice_id=audio.voice_id)


@router.post("/books", response_model=BookAudioRead, status_code=status.HTTP_201_CREATED, summary="Create one book audio record manually")
def create_book_audio(payload: BookAudioCreate, session: Session = Depends(get_session)) -> BookAudio:
    get_book_or_404(session, payload.book_id)
    get_voice_or_404(session, payload.voice_id)
    validate_script_source(payload.script_source)
    validate_audio_approval_status(payload.approval_status)
    validate_audio_provider(payload.provider)
    audio = BookAudio.model_validate(payload)
    audio = persist_book_audio(session, audio)
    if audio.is_active:
        audio = activate_book_audio(session, audio=audio)
    return _sync_audio_after_write(session, audio)


@router.get("/books/{audio_id}", response_model=BookAudioRead, summary="Get one book audio record")
def get_audio(audio_id: int, session: Session = Depends(get_session)) -> BookAudio:
    return get_book_audio_or_404(session, audio_id)


@router.patch("/books/{audio_id}", response_model=BookAudioRead, summary="Partially update one book audio record")
def update_book_audio(
    audio_id: int,
    payload: BookAudioUpdate,
    session: Session = Depends(get_session),
) -> BookAudio:
    audio = get_book_audio_or_404(session, audio_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "book_id" in update_data and update_data["book_id"] is not None:
        get_book_or_404(session, update_data["book_id"])
    if "voice_id" in update_data and update_data["voice_id"] is not None:
        get_voice_or_404(session, update_data["voice_id"])
    if "script_source" in update_data and update_data["script_source"] is not None:
        validate_script_source(update_data["script_source"])
    if "approval_status" in update_data and update_data["approval_status"] is not None:
        validate_audio_approval_status(update_data["approval_status"])
    if "provider" in update_data and update_data["provider"] is not None:
        validate_audio_provider(update_data["provider"])
    for field_name, value in update_data.items():
        setattr(audio, field_name, value)
    audio.updated_at = utc_now()
    audio = persist_book_audio(session, audio)
    if audio.is_active:
        audio = activate_book_audio(session, audio=audio)
    return _sync_audio_after_write(session, audio)


@router.delete("/books/{audio_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete one book audio record")
def delete_book_audio(audio_id: int, session: Session = Depends(get_session)) -> Response:
    audio = get_book_audio_or_404(session, audio_id)
    book = get_book_or_404(session, audio.book_id)
    session.delete(audio)
    session.commit()
    refresh_book_audio_available(session, book=book)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/books/{audio_id}/approve", response_model=BookAudioRead, summary="Approve a book audio version")
def approve_audio(
    audio_id: int,
    request: Request,
    payload: BookAudioApprovalRequest,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> BookAudio:
    audio = get_book_audio_or_404(session, audio_id)
    approved = approve_book_audio(
        session,
        audio=audio,
        generation_notes=payload.generation_notes,
        make_active=payload.make_active,
    )
    create_audit_log(
        session,
        action_type="audio_approved",
        entity_type="book_audio",
        entity_id=str(approved.id),
        summary=f"Approved audio {approved.id} for book {approved.book_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": approved.book_id, "make_active": payload.make_active},
    )
    return approved


@router.post("/books/{audio_id}/reject", response_model=BookAudioRead, summary="Reject a book audio version")
def reject_audio(
    audio_id: int,
    request: Request,
    payload: BookAudioApprovalRequest | None = None,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> BookAudio:
    audio = get_book_audio_or_404(session, audio_id)
    notes = payload.generation_notes if payload is not None else None
    rejected = reject_book_audio(session, audio=audio, generation_notes=notes)
    create_audit_log(
        session,
        action_type="audio_rejected",
        entity_type="book_audio",
        entity_id=str(rejected.id),
        summary=f"Rejected audio {rejected.id} for book {rejected.book_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": rejected.book_id, "generation_notes": notes},
    )
    return rejected


@router.post("/books/{audio_id}/activate", response_model=BookAudioRead, summary="Activate a book audio version")
def activate_audio(
    audio_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> BookAudio:
    audio = get_book_audio_or_404(session, audio_id)
    audio.is_active = True
    audio.updated_at = utc_now()
    audio = persist_book_audio(session, audio)
    audio = activate_book_audio(session, audio=audio)
    active_audio = _sync_audio_after_write(session, audio)
    create_audit_log(
        session,
        action_type="audio_activated",
        entity_type="book_audio",
        entity_id=str(active_audio.id),
        summary=f"Activated audio {active_audio.id} for book {active_audio.book_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": active_audio.book_id, "voice_id": active_audio.voice_id},
    )
    return active_audio
