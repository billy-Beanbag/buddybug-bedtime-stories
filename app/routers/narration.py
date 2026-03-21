from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.narration_schema import (
    AvailableVoicesResponse,
    NarrationGenerateRequest,
    NarrationGenerateResponse,
    ReaderNarrationResponse,
)
from app.services.achievement_service import handle_narrated_story_started
from app.services.audit_service import create_audit_log
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.narration_service import (
    fetch_reader_narration,
    generate_book_narration,
    list_available_voices,
    list_book_narrations,
)
from app.utils.dependencies import get_current_admin_user, get_current_active_user, get_optional_current_user

router = APIRouter(prefix="/narration", tags=["narration"])
admin_router = APIRouter(prefix="/admin/narration", tags=["admin-narration"])


@router.get("/voices", response_model=AvailableVoicesResponse, summary="List available narration voices")
def get_narration_voices(
    language: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> AvailableVoicesResponse:
    if child_profile_id is not None:
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for child profile context")
        validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    return AvailableVoicesResponse(
        voices=list_available_voices(
            session,
            language=language,
            user=current_user,
            child_profile_id=child_profile_id,
        )
    )


@router.get("/books/{book_id}", response_model=ReaderNarrationResponse, summary="Get narration for the reader")
def get_reader_narration(
    book_id: int,
    language: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    voice_key: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> ReaderNarrationResponse:
    if child_profile_id is not None:
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for child profile context")
        validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    response = fetch_reader_narration(
        session,
        book_id=book_id,
        language=language,
        user=current_user,
        child_profile_id=child_profile_id,
        voice_key=voice_key,
    )
    if current_user is not None:
        handle_narrated_story_started(
            session,
            user=current_user,
            child_profile_id=child_profile_id,
            source_table="booknarration",
            source_id=str(response.narration.id),
        )
    return response


@router.post(
    "/books/{book_id}/generate",
    response_model=NarrationGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate narration for one book",
)
def generate_reader_narration(
    book_id: int,
    payload: NarrationGenerateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> NarrationGenerateResponse:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Narration generation is admin-only for now")
    if payload.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="book_id mismatch")
    narration, segments, _voice = generate_book_narration(
        session,
        book_id=book_id,
        voice_key=payload.voice_key,
        language=payload.language,
        replace_existing=payload.replace_existing,
        actor_user=current_user,
    )
    return NarrationGenerateResponse(narration=narration, segments=segments)


@admin_router.post(
    "/books/{book_id}/generate",
    response_model=NarrationGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin generate narration for one book",
)
def admin_generate_narration(
    book_id: int,
    payload: NarrationGenerateRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> NarrationGenerateResponse:
    if payload.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="book_id mismatch")
    narration, segments, voice = generate_book_narration(
        session,
        book_id=book_id,
        voice_key=payload.voice_key,
        language=payload.language,
        replace_existing=payload.replace_existing,
        actor_user=current_user,
    )
    create_audit_log(
        session,
        action_type="book_narration_generated",
        entity_type="book_narration",
        entity_id=str(narration.id),
        summary=f"Generated narration for book {book_id} with voice {voice.key}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": book_id, "voice_key": voice.key, "language": payload.language},
    )
    return NarrationGenerateResponse(narration=narration, segments=segments)


@admin_router.get("/books/{book_id}", response_model=list[ReaderNarrationResponse], summary="List narrations for one book")
def admin_get_book_narrations(
    book_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[ReaderNarrationResponse]:
    return list_book_narrations(session, book_id=book_id)
