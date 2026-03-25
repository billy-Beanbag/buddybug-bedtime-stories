from fastapi import HTTPException, status
from sqlmodel import Session, desc, select

from app.models import Book, BookPage, ReadingProgress, User
from app.services.review_service import utc_now
from app.services.subscription_service import get_preview_page_limit, has_premium_access


def _published_book_statement():
    return select(Book).where(Book.published.is_(True), Book.publication_status == "published")


def get_book_or_404(session: Session, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


def get_published_book_or_404(session: Session, book_id: int) -> Book:
    statement = _published_book_statement().where(Book.id == book_id)
    book = session.exec(statement).first()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published book not found")
    return book


def get_published_books(
    session: Session,
    *,
    age_band: str | None,
    content_lane_key: str | None,
    language: str | None,
    limit: int,
) -> list[Book]:
    statement = _published_book_statement().order_by(Book.updated_at.desc()).limit(limit)
    if age_band:
        statement = statement.where(Book.age_band == age_band)
    if content_lane_key:
        statement = statement.where(Book.content_lane_key == content_lane_key)
    if language:
        statement = statement.where(Book.language == language)
    return list(session.exec(statement).all())


def get_book_pages(session: Session, book_id: int) -> list[BookPage]:
    return list(
        session.exec(select(BookPage).where(BookPage.book_id == book_id).order_by(BookPage.page_number)).all()
    )


def filter_pages_for_reader_access(pages: list[BookPage], current_user: User | None) -> list[BookPage]:
    if has_premium_access(current_user):
        return pages
    preview_page_limit = get_preview_page_limit(current_user)
    return [page for page in pages if page.page_number <= preview_page_limit]


def get_reader_book_detail(
    session: Session,
    book_id: int,
    *,
    current_user: User | None = None,
    apply_access_control: bool = False,
    allow_unpublished: bool = False,
) -> tuple[Book, list[BookPage]]:
    book = get_book_or_404(session, book_id) if allow_unpublished else get_published_book_or_404(session, book_id)
    pages = get_book_pages(session, book.id)
    if apply_access_control:
        pages = filter_pages_for_reader_access(pages, current_user)
    return book, pages


def get_book_page(
    session: Session,
    book_id: int,
    page_number: int,
    *,
    current_user: User | None = None,
    apply_access_control: bool = False,
) -> BookPage:
    get_published_book_or_404(session, book_id)
    if apply_access_control and not has_premium_access(current_user):
        preview_page_limit = get_preview_page_limit(current_user)
        if page_number > preview_page_limit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book page not found")
    statement = select(BookPage).where(BookPage.book_id == book_id, BookPage.page_number == page_number)
    page = session.exec(statement).first()
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book page not found")
    return page


def get_progress_by_reader_and_book(
    session: Session,
    *,
    reader_identifier: str,
    book_id: int,
    child_profile_id: int | None = None,
) -> ReadingProgress | None:
    statement = select(ReadingProgress).where(
        ReadingProgress.reader_identifier == reader_identifier,
        ReadingProgress.book_id == book_id,
    )
    if child_profile_id is None:
        statement = statement.where(ReadingProgress.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(ReadingProgress.child_profile_id == child_profile_id)
    return session.exec(statement).first()


def _max_page_number(session: Session, book_id: int) -> int:
    statement = select(BookPage).where(BookPage.book_id == book_id).order_by(desc(BookPage.page_number))
    page = session.exec(statement).first()
    if page is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book has no pages")
    return page.page_number


def mark_book_completed_if_last_page(
    session: Session,
    *,
    book_id: int,
    current_page_number: int,
) -> bool:
    max_page_number = _max_page_number(session, book_id)
    return current_page_number >= max_page_number


def upsert_reading_progress(
    session: Session,
    *,
    reader_identifier: str,
    book_id: int,
    child_profile_id: int | None,
    current_page_number: int,
    completed: bool,
) -> ReadingProgress:
    if not reader_identifier.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="reader_identifier is required")
    if current_page_number < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="current_page_number must be non-negative")

    get_published_book_or_404(session, book_id)
    auto_completed = mark_book_completed_if_last_page(
        session, book_id=book_id, current_page_number=current_page_number
    )

    progress = get_progress_by_reader_and_book(
        session,
        reader_identifier=reader_identifier,
        book_id=book_id,
        child_profile_id=child_profile_id,
    )
    now = utc_now()
    if progress is None:
        progress = ReadingProgress(
            reader_identifier=reader_identifier.strip(),
            book_id=book_id,
            child_profile_id=child_profile_id,
            current_page_number=current_page_number,
            completed=completed or auto_completed,
            last_opened_at=now,
        )
    else:
        progress.current_page_number = current_page_number
        progress.completed = completed or auto_completed
        progress.last_opened_at = now
        progress.updated_at = now

    session.add(progress)
    session.commit()
    session.refresh(progress)
    return progress


def update_reading_progress(
    session: Session,
    *,
    progress: ReadingProgress,
    child_profile_id: int | None,
    current_page_number: int | None,
    completed: bool | None,
) -> ReadingProgress:
    if child_profile_id is not None:
        progress.child_profile_id = child_profile_id
    if current_page_number is not None:
        if current_page_number < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="current_page_number must be non-negative")
        progress.current_page_number = current_page_number

    auto_completed = mark_book_completed_if_last_page(
        session,
        book_id=progress.book_id,
        current_page_number=progress.current_page_number,
    )
    progress.completed = auto_completed if completed is None else (completed or auto_completed)
    progress.last_opened_at = utc_now()
    progress.updated_at = utc_now()

    session.add(progress)
    session.commit()
    session.refresh(progress)
    return progress


def get_reading_progress_or_404(session: Session, progress_id: int) -> ReadingProgress:
    progress = session.get(ReadingProgress, progress_id)
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading progress not found")
    return progress


def get_continue_reading(
    session: Session,
    *,
    reader_identifier: str,
    child_profile_id: int | None = None,
) -> list[tuple[ReadingProgress, Book]]:
    statement = (
        select(ReadingProgress)
        .where(ReadingProgress.reader_identifier == reader_identifier)
        .order_by(ReadingProgress.last_opened_at.desc())
    )
    if child_profile_id is None:
        statement = statement.where(ReadingProgress.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(ReadingProgress.child_profile_id == child_profile_id)
    progresses = list(session.exec(statement).all())
    results: list[tuple[ReadingProgress, Book]] = []
    for progress in progresses:
        book_statement = _published_book_statement().where(Book.id == progress.book_id)
        book = session.exec(book_statement).first()
        if book is not None:
            results.append((progress, book))
    return results
