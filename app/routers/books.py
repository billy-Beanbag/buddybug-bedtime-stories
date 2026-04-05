from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import Book, BookPage, StoryDraft, StoryPage, User
from app.services.audit_service import create_audit_log
from app.schemas.book_schema import (
    BookAssemblyRequest,
    BookAssemblyResponse,
    BookCreate,
    BookDetailResponse,
    BookPageRead,
    BookPageUpdate,
    BookRead,
    BookUpdate,
)
from app.services.book_builder import (
    assemble_book_from_draft,
    get_book_or_404,
    get_story_draft_or_404,
    validate_story_pages_ready_for_release,
    validate_publication_status,
)
from app.services.narration_service import auto_generate_default_narration_for_book
from app.services.review_service import utc_now
from app.utils.dependencies import get_current_admin_user, get_current_editor_user

router = APIRouter(prefix="/books", tags=["books"])


def _persist_book(session: Session, book: Book) -> Book:
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def _get_book_pages(session: Session, book_id: int) -> list[BookPage]:
    return list(
        session.exec(select(BookPage).where(BookPage.book_id == book_id).order_by(BookPage.page_number)).all()
    )


def _delete_book_with_pages(session: Session, book: Book) -> None:
    for page in _get_book_pages(session, book.id):
        session.delete(page)
    session.delete(book)
    session.commit()


@router.get("", response_model=list[BookRead], summary="List assembled books")
def list_books(
    published: bool | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    story_draft_id: int | None = Query(default=None),
    age_band: str | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    is_classic: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
) -> list[Book]:
    statement = select(Book).order_by(Book.created_at.desc()).limit(limit)
    if published is not None:
        statement = statement.where(Book.published == published)
    if publication_status:
        validate_publication_status(publication_status)
        statement = statement.where(Book.publication_status == publication_status)
    if story_draft_id is not None:
        statement = statement.where(Book.story_draft_id == story_draft_id)
    if age_band is not None:
        statement = statement.where(Book.age_band == age_band)
    if content_lane_key is not None:
        statement = statement.where(Book.content_lane_key == content_lane_key)
    if is_classic is not None:
        statement = statement.where(Book.is_classic == is_classic)
    return list(session.exec(statement).all())


@router.get("/by-draft/{story_draft_id}", response_model=BookRead, summary="Get the assembled book for one draft")
def get_book_by_draft(story_draft_id: int, session: Session = Depends(get_session)) -> Book:
    statement = select(Book).where(Book.story_draft_id == story_draft_id)
    book = session.exec(statement).first()
    if book is None:
        get_story_draft_or_404(session, story_draft_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found for this story draft")
    return book


@router.post(
    "/assemble",
    response_model=BookAssemblyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assemble a final book from an approved draft and story pages",
)
def assemble_book(
    payload: BookAssemblyRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> BookAssemblyResponse:
    book, pages = assemble_book_from_draft(
        session,
        story_draft_id=payload.story_draft_id,
        language=payload.language,
        content_lane_key=payload.content_lane_key,
        publish_immediately=payload.publish_immediately,
        replace_existing=payload.replace_existing,
    )
    return BookAssemblyResponse(book=book, page_count=len(pages), pages=pages)


@router.get("/{book_id}", response_model=BookRead, summary="Get one book by id")
def get_book(book_id: int, session: Session = Depends(get_session)) -> Book:
    return get_book_or_404(session, book_id)


@router.get("/{book_id}/detail", response_model=BookDetailResponse, summary="Get a book with ordered pages")
def get_book_detail(book_id: int, session: Session = Depends(get_session)) -> BookDetailResponse:
    book = get_book_or_404(session, book_id)
    pages = _get_book_pages(session, book.id)
    return BookDetailResponse(book=book, pages=pages)


@router.get(
    "/{book_id}/story-draft-id",
    summary="Get story_draft_id for a book (for preview rebuild)",
)
def get_book_story_draft_id(
    book_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> dict:
    """Return story_draft_id for a book. Used when reader response lacks it."""
    book = get_book_or_404(session, book_id)
    return {"story_draft_id": book.story_draft_id}


@router.get("/{book_id}/pages", response_model=list[BookPageRead], summary="Get ordered pages for one book")
def get_book_pages(book_id: int, session: Session = Depends(get_session)) -> list[BookPage]:
    get_book_or_404(session, book_id)
    return _get_book_pages(session, book_id)


@router.patch(
    "/{book_id}/pages/{page_number}",
    response_model=BookPageRead,
    summary="Partially update one book page",
)
def update_book_page(
    book_id: int,
    page_number: int,
    payload: BookPageUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> BookPage:
    get_book_or_404(session, book_id)
    book_page = next((page for page in _get_book_pages(session, book_id) if page.page_number == page_number), None)
    if book_page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book page not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(book_page, field_name, value)

    book_page.updated_at = utc_now()
    session.add(book_page)
    session.commit()
    session.refresh(book_page)
    return book_page


@router.get(
    "/{book_id}/pages/{page_number}/source-story-page",
    summary="Get source story page id for a book page (for preview review)",
)
def get_book_page_source_story_page(
    book_id: int,
    page_number: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> dict:
    """Return source_story_page_id for a book page. Falls back to draft order when null (legacy previews)."""
    book = get_book_or_404(session, book_id)
    pages = _get_book_pages(session, book_id)
    book_page = next((p for p in pages if p.page_number == page_number), None)
    if book_page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book page not found")
    if book_page.source_story_page_id is not None:
        return {"source_story_page_id": book_page.source_story_page_id}
    if page_number <= 0:
        return {"source_story_page_id": None}
    story_pages = list(
        session.exec(select(StoryPage).where(StoryPage.story_draft_id == book.story_draft_id).order_by(StoryPage.page_number))
    )
    match = next((sp for sp in story_pages if sp.page_number == page_number), None)
    if match is None:
        page_index = next((i for i, p in enumerate(pages) if p.page_number == page_number), -1)
        if page_index > 0 and page_index <= len(story_pages):
            match = story_pages[page_index - 1]
    return {"source_story_page_id": match.id if match else None}


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED, summary="Create one book manually")
def create_book(
    payload: BookCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Book:
    story_draft = get_story_draft_or_404(session, payload.story_draft_id)
    validate_publication_status(payload.publication_status)
    book = Book.model_validate(
        payload.model_copy(update={"content_lane_key": payload.content_lane_key or story_draft.content_lane_key})
    )
    return _persist_book(session, book)


@router.patch("/{book_id}", response_model=BookRead, summary="Partially update one book")
def update_book(
    book_id: int,
    payload: BookUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Book:
    book = get_book_or_404(session, book_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "story_draft_id" in update_data and update_data["story_draft_id"] is not None:
        story_draft = get_story_draft_or_404(session, update_data["story_draft_id"])
        if "content_lane_key" not in update_data:
            update_data["content_lane_key"] = story_draft.content_lane_key
    if "publication_status" in update_data and update_data["publication_status"] is not None:
        validate_publication_status(update_data["publication_status"])

    for field_name, value in update_data.items():
        setattr(book, field_name, value)

    book.updated_at = utc_now()
    return _persist_book(session, book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete one book and its pages")
def delete_book(
    book_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Response:
    book = get_book_or_404(session, book_id)
    _delete_book_with_pages(session, book)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{book_id}/publish", response_model=BookRead, summary="Publish a book")
def publish_book(
    book_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Book:
    book = get_book_or_404(session, book_id)
    book_pages = _get_book_pages(session, book.id)
    if len(book_pages) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book must include story pages before publishing")
    if any(not (page.text_content or "").strip() for page in book_pages if page.page_number > 0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book pages must contain text before publishing")
    story_draft = session.get(StoryDraft, book.story_draft_id)
    if story_draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")
    validate_story_pages_ready_for_release(
        session,
        story_pages=session.exec(
            select(StoryPage)
            .where(StoryPage.story_draft_id == story_draft.id)
            .order_by(StoryPage.page_number)
        ).all(),
    )
    existing_published = list(
        session.exec(
            select(Book).where(
                Book.story_draft_id == story_draft.id,
                Book.id != book.id,
                Book.published.is_(True),
            )
        ).all()
    )
    for existing in existing_published:
        existing.published = False
        existing.publication_status = "archived"
        existing.updated_at = utc_now()
        session.add(existing)
    book.title = story_draft.title
    book.age_band = story_draft.age_band
    book.language = story_draft.language
    book.content_lane_key = story_draft.content_lane_key
    book.published = True
    book.publication_status = "published"
    book.updated_at = utc_now()
    updated_book = _persist_book(session, book)
    create_audit_log(
        session,
        action_type="book_published",
        entity_type="book",
        entity_id=str(updated_book.id),
        summary=f"Published book '{updated_book.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"publication_status": updated_book.publication_status},
    )
    auto_generate_default_narration_for_book(session, book=updated_book, replace_existing=False)
    return updated_book


@router.post("/{book_id}/archive", response_model=BookRead, summary="Archive a book")
def archive_book(
    book_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Book:
    book = get_book_or_404(session, book_id)
    book.published = False
    book.publication_status = "archived"
    book.updated_at = utc_now()
    updated_book = _persist_book(session, book)
    create_audit_log(
        session,
        action_type="book_archived",
        entity_type="book",
        entity_id=str(updated_book.id),
        summary=f"Archived book '{updated_book.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"publication_status": updated_book.publication_status},
    )
    return updated_book
