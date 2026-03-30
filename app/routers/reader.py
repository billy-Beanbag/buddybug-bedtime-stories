from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import StoryPage, User
from app.schemas.i18n_schema import LocalizedReaderBookDetail, SupportedLanguagesResponse
from app.schemas.reader_schema import (
    ContinueReadingResponse,
    ReaderBookSummary,
    ReaderPageRead,
    ReadingProgressCreate,
    ReadingProgressRead,
    ReadingProgressUpdate,
)
from app.services.analytics_service import track_event_safe
from app.services.achievement_service import handle_story_completed, update_reading_streak
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.i18n_service import (
    build_localized_book_summaries,
    get_books_with_language_preference,
    get_localized_book_detail,
    get_localized_reader_book_page,
    get_localized_reader_pages,
    get_supported_languages,
)
from app.services.parental_controls_service import is_age_band_allowed, resolve_parental_controls
from app.services.reader_service import (
    get_book_or_404,
    get_book_pages,
    get_continue_reading,
    get_published_books,
    get_reading_progress_or_404,
    get_progress_by_reader_and_book,
    update_reading_progress,
    upsert_reading_progress,
)
from app.utils.dependencies import get_current_editor_user, get_optional_current_user

router = APIRouter(prefix="/reader", tags=["reader"])


def _resolve_child_profile(
    session: Session,
    *,
    current_user: User | None,
    child_profile_id: int | None,
):
    if child_profile_id is None:
        return None
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required for child profile context")
    return validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)


def _resolve_controls(session: Session, *, current_user: User | None, child_profile_id: int | None):
    if current_user is None:
        return None
    return resolve_parental_controls(session, user=current_user, child_profile_id=child_profile_id)


def _is_book_allowed_for_reader(book, *, controls) -> bool:
    return is_age_band_allowed(requested_age_band=book.age_band, controls=controls)


@router.get("/books", response_model=list[ReaderBookSummary], summary="List published books for reading")
def list_reader_books(
    age_band: str | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    language: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[ReaderBookSummary]:
    child_profile = _resolve_child_profile(
        session,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    effective_age_band = child_profile.age_band if child_profile is not None else age_band
    effective_language = child_profile.language if child_profile is not None else language
    controls = _resolve_controls(
        session,
        current_user=current_user,
        child_profile_id=child_profile.id if child_profile is not None else None,
    )
    books = get_published_books(
        session,
        age_band=effective_age_band,
        content_lane_key=content_lane_key,
        language=None,
        limit=limit,
    )
    pre_filter_count = len(books)
    if controls is not None:
        books = [book for book in books if _is_book_allowed_for_reader(book, controls=controls)]
    if controls is not None and len(books) != pre_filter_count:
        track_event_safe(
            session,
            event_name="age_band_filtered_by_parental_controls",
            user=current_user,
            child_profile_id=child_profile.id if child_profile is not None else None,
            metadata={"before_count": pre_filter_count, "after_count": len(books)},
        )
    books = get_books_with_language_preference(session, books=books, requested_language=effective_language)
    page_count_lookup = {book.id: len(get_book_pages(session, book.id)) for book in books}
    return build_localized_book_summaries(
        session,
        books=books[:limit],
        requested_language=effective_language,
        page_count_lookup=page_count_lookup,
    )


@router.get("/books/{book_id}", response_model=LocalizedReaderBookDetail, summary="Get one published book for reading")
def get_reader_book(
    book_id: int,
    language: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    x_reader_identifier: str | None = Header(default=None, alias="X-Reader-Identifier"),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> LocalizedReaderBookDetail:
    child_profile = _resolve_child_profile(
        session,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    controls = _resolve_controls(
        session,
        current_user=current_user,
        child_profile_id=child_profile.id if child_profile is not None else None,
    )
    if controls is not None:
        from app.services.reader_service import get_published_book_or_404

        book = get_published_book_or_404(session, book_id)
        if not _is_book_allowed_for_reader(book, controls=controls):
            track_event_safe(
                session,
                event_name="age_band_filtered_by_parental_controls",
                user=current_user,
                child_profile_id=child_profile.id if child_profile is not None else None,
                book_id=book_id,
                metadata={"source": "reader_book_blocked"},
            )
            raise HTTPException(status_code=403, detail="This story is unavailable with the current parental controls")
    effective_language = child_profile.language if child_profile is not None else language
    detail = get_localized_book_detail(
        session,
        book_id,
        requested_language=effective_language,
        current_user=current_user,
        apply_access_control=True,
    )
    track_event_safe(
        session,
        event_name="book_opened",
        user=current_user,
        child_profile_id=child_profile.id if child_profile is not None else None,
        reader_identifier=x_reader_identifier,
        book_id=book_id,
        language=effective_language or detail.language,
        metadata={"source": "backend_reader_endpoint"},
    )
    if controls is not None and controls.bedtime_mode_enabled:
        track_event_safe(
            session,
            event_name="bedtime_mode_used",
            user=current_user,
            child_profile_id=child_profile.id if child_profile is not None else None,
            book_id=book_id,
            metadata={"source": "backend_reader_endpoint"},
        )
    return detail


@router.get(
    "/books/{book_id}/story-draft-id",
    summary="Get story_draft_id for a book (for preview rebuild)",
)
def get_reader_book_story_draft_id(
    book_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> dict:
    """Return story_draft_id for a book. Used when reader response lacks it."""
    book = get_book_or_404(session, book_id)
    return {"story_draft_id": book.story_draft_id}


@router.get(
    "/books/{book_id}/pages/{page_number}/source-story-page",
    summary="Get source story page id for a book page (for preview review)",
)
def get_reader_page_source_story_page(
    book_id: int,
    page_number: int,
    page_index: int | None = Query(default=None, description="0-based index in book.pages (fallback when page_number match fails)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> dict:
    """Return source_story_page_id for a book page. Falls back to draft order when null."""
    book = get_book_or_404(session, book_id)
    pages = get_book_pages(session, book_id)
    book_page = next((p for p in pages if p.page_number == page_number), None)
    if book_page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book page not found")
    if book_page.source_story_page_id is not None:
        return {"source_story_page_id": book_page.source_story_page_id}
    if page_number <= 0:
        return {"source_story_page_id": None}
    story_pages = list(
        session.exec(
            select(StoryPage)
            .where(StoryPage.story_draft_id == book.story_draft_id)
            .order_by(StoryPage.page_number)
        )
    )
    match = next((sp for sp in story_pages if sp.page_number == page_number), None)
    if match is None:
        idx = next((i for i, p in enumerate(pages) if p.page_number == page_number), -1)
        if idx < 0 and page_index is not None:
            idx = page_index
        if idx > 0 and idx <= len(story_pages):
            match = story_pages[idx - 1]
    return {"source_story_page_id": match.id if match else None}


@router.get(
    "/books/{book_id}/preview",
    response_model=LocalizedReaderBookDetail,
    summary="Get one assembled book for internal preview",
)
def get_reader_book_preview(
    book_id: int,
    language: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> LocalizedReaderBookDetail:
    return get_localized_book_detail(
        session,
        book_id,
        requested_language=language,
        current_user=current_user,
        apply_access_control=False,
        allow_unpublished=True,
    )


@router.get(
    "/books/{book_id}/pages",
    response_model=list[ReaderPageRead],
    summary="Get ordered reader pages for one published book",
)
def get_reader_book_pages(
    book_id: int,
    language: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[ReaderPageRead]:
    child_profile = _resolve_child_profile(
        session,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    controls = _resolve_controls(
        session,
        current_user=current_user,
        child_profile_id=child_profile.id if child_profile is not None else None,
    )
    if controls is not None:
        from app.services.reader_service import get_published_book_or_404

        book = get_published_book_or_404(session, book_id)
        if not _is_book_allowed_for_reader(book, controls=controls):
            raise HTTPException(status_code=403, detail="This story is unavailable with the current parental controls")
    pages, _ = get_localized_reader_pages(
        session,
        book_id,
        requested_language=child_profile.language if child_profile is not None else language,
        current_user=current_user,
        apply_access_control=True,
    )
    return pages


@router.get(
    "/books/{book_id}/pages/{page_number}",
    response_model=ReaderPageRead,
    summary="Get one page from a published book by page number",
)
def get_reader_page(
    book_id: int,
    page_number: int,
    language: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> ReaderPageRead:
    child_profile = _resolve_child_profile(
        session,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    controls = _resolve_controls(
        session,
        current_user=current_user,
        child_profile_id=child_profile.id if child_profile is not None else None,
    )
    if controls is not None:
        from app.services.reader_service import get_published_book_or_404

        book = get_published_book_or_404(session, book_id)
        if not _is_book_allowed_for_reader(book, controls=controls):
            raise HTTPException(status_code=403, detail="This story is unavailable with the current parental controls")
    return get_localized_reader_book_page(
        session,
        book_id=book_id,
        page_number=page_number,
        requested_language=child_profile.language if child_profile is not None else language,
        current_user=current_user,
        apply_access_control=True,
    )


@router.get("/progress", response_model=ReadingProgressRead, summary="Get reading progress for one reader/book pair")
def get_reader_progress(
    reader_identifier: str = Query(...),
    book_id: int = Query(...),
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> ReadingProgressRead:
    _resolve_child_profile(session, current_user=current_user, child_profile_id=child_profile_id)
    progress = get_progress_by_reader_and_book(
        session,
        reader_identifier=reader_identifier,
        book_id=book_id,
        child_profile_id=child_profile_id,
    )
    if progress is None:
        raise HTTPException(status_code=404, detail="Reading progress not found")
    return progress


@router.post("/progress", response_model=ReadingProgressRead, summary="Create or update reading progress")
def create_or_update_reader_progress(
    payload: ReadingProgressCreate,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> ReadingProgressRead:
    child_profile = _resolve_child_profile(
        session,
        current_user=current_user,
        child_profile_id=payload.child_profile_id,
    )
    previous_progress = get_progress_by_reader_and_book(
        session,
        reader_identifier=payload.reader_identifier,
        book_id=payload.book_id,
        child_profile_id=payload.child_profile_id,
    )
    was_completed = previous_progress.completed if previous_progress is not None else False
    progress = upsert_reading_progress(
        session,
        reader_identifier=payload.reader_identifier,
        book_id=payload.book_id,
        child_profile_id=payload.child_profile_id,
        current_page_number=payload.current_page_number,
        completed=payload.completed,
    )
    if current_user is not None:
        update_reading_streak(
            session,
            user=current_user,
            child_profile_id=payload.child_profile_id,
            read_at=progress.last_opened_at,
        )
    if progress.completed and not was_completed:
        if current_user is not None:
            handle_story_completed(
                session,
                user=current_user,
                child_profile_id=payload.child_profile_id,
                source_table="readingprogress",
                source_id=str(progress.id),
                occurred_at=progress.last_opened_at,
            )
        track_event_safe(
            session,
            event_name="book_completed",
            user=current_user,
            child_profile_id=child_profile.id if child_profile is not None else None,
            reader_identifier=payload.reader_identifier,
            book_id=payload.book_id,
            metadata={"source": "backend_progress_upsert", "page_number": progress.current_page_number},
        )
    return progress


@router.patch("/progress/{progress_id}", response_model=ReadingProgressRead, summary="Update reading progress")
def patch_reader_progress(
    progress_id: int,
    payload: ReadingProgressUpdate,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> ReadingProgressRead:
    progress = get_reading_progress_or_404(session, progress_id)
    child_profile = _resolve_child_profile(
        session,
        current_user=current_user,
        child_profile_id=payload.child_profile_id if payload.child_profile_id is not None else progress.child_profile_id,
    )
    was_completed = progress.completed
    updated_progress = update_reading_progress(
        session,
        progress=progress,
        child_profile_id=payload.child_profile_id if payload.child_profile_id is not None else progress.child_profile_id,
        current_page_number=payload.current_page_number,
        completed=payload.completed,
    )
    effective_child_profile_id = (
        payload.child_profile_id if payload.child_profile_id is not None else progress.child_profile_id
    )
    if current_user is not None:
        update_reading_streak(
            session,
            user=current_user,
            child_profile_id=effective_child_profile_id,
            read_at=updated_progress.last_opened_at,
        )
    if updated_progress.completed and not was_completed:
        if current_user is not None:
            handle_story_completed(
                session,
                user=current_user,
                child_profile_id=effective_child_profile_id,
                source_table="readingprogress",
                source_id=str(updated_progress.id),
                occurred_at=updated_progress.last_opened_at,
            )
        track_event_safe(
            session,
            event_name="book_completed",
            user=current_user,
            child_profile_id=child_profile.id if child_profile is not None else progress.child_profile_id,
            reader_identifier=updated_progress.reader_identifier,
            book_id=updated_progress.book_id,
            metadata={"source": "backend_progress_patch", "page_number": updated_progress.current_page_number},
        )
    return updated_progress


@router.get(
    "/languages",
    response_model=SupportedLanguagesResponse,
    summary="Get supported UI and content languages",
)
def get_reader_languages() -> SupportedLanguagesResponse:
    return get_supported_languages()


@router.get(
    "/continue",
    response_model=list[ContinueReadingResponse],
    summary="List continue-reading entries for a reader",
)
def get_continue_reading_entries(
    reader_identifier: str = Query(...),
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[ContinueReadingResponse]:
    _resolve_child_profile(session, current_user=current_user, child_profile_id=child_profile_id)
    entries = get_continue_reading(
        session,
        reader_identifier=reader_identifier,
        child_profile_id=child_profile_id,
    )
    return [
        ContinueReadingResponse(
            book_id=book.id,
            title=book.title,
            cover_image_url=book.cover_image_url,
            child_profile_id=progress.child_profile_id,
            current_page_number=progress.current_page_number,
            completed=progress.completed,
            last_opened_at=progress.last_opened_at,
        )
        for progress, book in entries
    ]
