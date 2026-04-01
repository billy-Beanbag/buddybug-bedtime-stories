from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, BookPage, BookPageTranslation, BookTranslation, StoryPage
from app.schemas.i18n_schema import LocalizedReaderBookDetail, SupportedLanguagesResponse
from app.schemas.reader_schema import ReaderPageRead
from app.services.reader_service import get_reader_book_detail

SUPPORTED_LANGUAGE_CODES = ["en", "es", "fr"]
DEFAULT_LANGUAGE = "en"


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE
    normalized = language.strip().lower()
    return normalized if normalized in SUPPORTED_LANGUAGE_CODES else DEFAULT_LANGUAGE


def validate_language_code(language: str | None) -> str:
    normalized = normalize_language(language)
    if language and language.strip().lower() not in SUPPORTED_LANGUAGE_CODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported language code")
    return normalized


def get_supported_languages() -> SupportedLanguagesResponse:
    return SupportedLanguagesResponse(
        supported_ui_languages=SUPPORTED_LANGUAGE_CODES,
        supported_content_languages=SUPPORTED_LANGUAGE_CODES,
        default_language=DEFAULT_LANGUAGE,
    )


def get_book_translation(
    session: Session,
    *,
    book_id: int,
    language: str,
    published_only: bool = True,
) -> BookTranslation | None:
    statement = select(BookTranslation).where(
        BookTranslation.book_id == book_id,
        BookTranslation.language == language,
    )
    if published_only:
        statement = statement.where(BookTranslation.published.is_(True))
    return session.exec(statement).first()


def get_book_page_translations_for_pages(
    session: Session,
    *,
    book_page_ids: list[int],
    language: str,
) -> dict[int, BookPageTranslation]:
    if not book_page_ids:
        return {}
    statement = select(BookPageTranslation).where(
        BookPageTranslation.book_page_id.in_(book_page_ids),
        BookPageTranslation.language == language,
    )
    return {
        translation.book_page_id: translation
        for translation in session.exec(statement).all()
    }


def get_published_book_translation_map(session: Session, *, language: str) -> dict[int, BookTranslation]:
    if language == DEFAULT_LANGUAGE:
        return {}
    statement = select(BookTranslation).where(
        BookTranslation.language == language,
        BookTranslation.published.is_(True),
    )
    return {translation.book_id: translation for translation in session.exec(statement).all()}


def resolve_book_language(book: Book, *, requested_language: str, has_translation: bool) -> str:
    if requested_language != DEFAULT_LANGUAGE and has_translation:
        return requested_language
    return book.language or DEFAULT_LANGUAGE


def _resolve_source_story_page_id(
    session: Session,
    *,
    book: Book,
    page: BookPage,
    ordered_pages: list[BookPage],
) -> int | None:
    """Backfill source_story_page_id when BookPage has it null (legacy previews)."""
    if page.source_story_page_id is not None:
        return page.source_story_page_id
    if page.page_number <= 0:
        return None
    story_pages = list(
        session.exec(
            select(StoryPage)
            .where(StoryPage.story_draft_id == book.story_draft_id)
            .order_by(StoryPage.page_number)
        )
    )
    match = next((sp for sp in story_pages if sp.page_number == page.page_number), None)
    if match is not None:
        return match.id
    page_index = next((i for i, p in enumerate(ordered_pages) if p.id == page.id), -1)
    if page_index > 0 and page_index <= len(story_pages):
        return story_pages[page_index - 1].id
    return None


def localize_reader_pages(
    session: Session,
    *,
    book: Book,
    pages: list[BookPage],
    requested_language: str,
) -> tuple[list[ReaderPageRead], bool]:
    if not pages:
        return [], False
    translation_map = get_book_page_translations_for_pages(
        session,
        book_page_ids=[page.id for page in pages],
        language=requested_language,
    )
    localized_pages = []
    for page in pages:
        source_id = page.source_story_page_id
        if source_id is None and page.page_number > 0:
            source_id = _resolve_source_story_page_id(session, book=book, page=page, ordered_pages=pages)
        localized_pages.append(
            ReaderPageRead(
                id=page.id,
                book_id=page.book_id,
                source_story_page_id=source_id,
                page_number=page.page_number,
                text_content=translation_map.get(page.id).text_content if page.id in translation_map else page.text_content,
                image_url=page.image_url,
                layout_type=page.layout_type,
            )
        )
    return localized_pages, bool(translation_map)


def get_localized_book_detail(
    session: Session,
    book_id: int,
    *,
    requested_language: str | None,
    current_user=None,
    apply_access_control: bool = False,
    allow_unpublished: bool = False,
) -> LocalizedReaderBookDetail:
    normalized_language = normalize_language(requested_language)
    book, pages = get_reader_book_detail(
        session,
        book_id,
        current_user=current_user,
        apply_access_control=apply_access_control,
        allow_unpublished=allow_unpublished,
    )
    translation = get_book_translation(session, book_id=book.id, language=normalized_language)
    localized_pages, has_page_translations = localize_reader_pages(
        session,
        book=book,
        pages=pages,
        requested_language=normalized_language,
    )
    resolved_language = resolve_book_language(
        book,
        requested_language=normalized_language,
        has_translation=translation is not None or has_page_translations,
    )
    page_mapping = {}
    for p in localized_pages:
        if p.page_number > 0 and p.source_story_page_id is not None:
            page_mapping[p.page_number] = p.source_story_page_id
    if not page_mapping and pages and book.story_draft_id:
        story_pages = list(
            session.exec(
                select(StoryPage)
                .where(StoryPage.story_draft_id == book.story_draft_id)
                .order_by(StoryPage.page_number)
            )
        )
        for i, bp in enumerate(pages):
            if bp.page_number > 0 and i > 0 and i - 1 < len(story_pages):
                page_mapping[bp.page_number] = story_pages[i - 1].id
    page_mapping = page_mapping if page_mapping else None
    return LocalizedReaderBookDetail(
        book_id=book.id,
        language=resolved_language,
        title=translation.title if translation is not None else book.title,
        cover_image_url=book.cover_image_url,
        age_band=book.age_band,
        content_lane_key=book.content_lane_key,
        published=book.published,
        publication_status=book.publication_status,
        pages=localized_pages,
        story_draft_id=book.story_draft_id,
        page_mapping=page_mapping,
    )


def get_localized_reader_pages(
    session: Session,
    book_id: int,
    *,
    requested_language: str | None,
    current_user=None,
    apply_access_control: bool = False,
    allow_unpublished: bool = False,
) -> tuple[list[ReaderPageRead], str]:
    normalized_language = normalize_language(requested_language)
    book, pages = get_reader_book_detail(
        session,
        book_id,
        current_user=current_user,
        apply_access_control=apply_access_control,
        allow_unpublished=allow_unpublished,
    )
    translation = get_book_translation(session, book_id=book.id, language=normalized_language)
    localized_pages, has_page_translations = localize_reader_pages(
        session,
        book=book,
        pages=pages,
        requested_language=normalized_language,
    )
    resolved_language = resolve_book_language(
        book,
        requested_language=normalized_language,
        has_translation=translation is not None or has_page_translations,
    )
    return localized_pages, resolved_language


def get_localized_reader_book_page(
    session: Session,
    *,
    book_id: int,
    page_number: int,
    requested_language: str | None,
    current_user=None,
    apply_access_control: bool = False,
    allow_unpublished: bool = False,
) -> ReaderPageRead:
    localized_pages, _ = get_localized_reader_pages(
        session,
        book_id,
        requested_language=requested_language,
        current_user=current_user,
        apply_access_control=apply_access_control,
        allow_unpublished=allow_unpublished,
    )
    for page in localized_pages:
        if page.page_number == page_number:
            return page
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book page not found")


def upsert_book_translation(
    session: Session,
    *,
    book_id: int,
    language: str,
    title: str,
    description: str | None,
    published: bool,
) -> BookTranslation:
    normalized_language = validate_language_code(language)
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    existing = session.exec(
        select(BookTranslation).where(
            BookTranslation.book_id == book_id,
            BookTranslation.language == normalized_language,
        )
    ).first()
    if existing is None:
        existing = BookTranslation(
            book_id=book_id,
            language=normalized_language,
            title=title,
            description=description,
            published=published,
        )
    else:
        existing.title = title
        existing.description = description
        existing.published = published
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


def upsert_book_page_translation(
    session: Session,
    *,
    book_page_id: int,
    language: str,
    text_content: str,
) -> BookPageTranslation:
    normalized_language = validate_language_code(language)
    existing = session.exec(
        select(BookPageTranslation).where(
            BookPageTranslation.book_page_id == book_page_id,
            BookPageTranslation.language == normalized_language,
        )
    ).first()
    if existing is None:
        existing = BookPageTranslation(
            book_page_id=book_page_id,
            language=normalized_language,
            text_content=text_content,
        )
    else:
        existing.text_content = text_content
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


def clone_book_to_language(session: Session, *, book: Book, language: str) -> tuple[BookTranslation, list[BookPageTranslation]]:
    normalized_language = validate_language_code(language)
    pages = list(session.exec(select(BookPage).where(BookPage.book_id == book.id).order_by(BookPage.page_number)).all())
    translation = upsert_book_translation(
        session,
        book_id=book.id,
        language=normalized_language,
        title=book.title,
        description=f"Placeholder {normalized_language.upper()} translation for {book.title}",
        published=False,
    )
    page_translations = [
        upsert_book_page_translation(
            session,
            book_page_id=page.id,
            language=normalized_language,
            text_content=page.text_content,
        )
        for page in pages
    ]
    return translation, page_translations


def get_books_with_language_preference(
    session: Session,
    *,
    books: list[Book],
    requested_language: str | None,
) -> list[Book]:
    normalized_language = normalize_language(requested_language)
    if normalized_language == DEFAULT_LANGUAGE:
        return books
    translation_map = get_published_book_translation_map(session, language=normalized_language)
    return sorted(
        books,
        key=lambda book: (
            0 if book.id in translation_map or book.language == normalized_language else 1,
            -book.updated_at.timestamp(),
        ),
    )


def build_localized_book_summaries(
    session: Session,
    *,
    books: list[Book],
    requested_language: str | None,
    page_count_lookup: dict[int, int],
):
    from app.schemas.reader_schema import ReaderBookSummary

    normalized_language = normalize_language(requested_language)
    translation_map = get_published_book_translation_map(session, language=normalized_language)
    summaries: list[ReaderBookSummary] = []
    for book in books:
        translation = translation_map.get(book.id)
        summaries.append(
            ReaderBookSummary(
                book_id=book.id,
                title=translation.title if translation is not None else book.title,
                cover_image_url=book.cover_image_url,
                age_band=book.age_band,
                content_lane_key=book.content_lane_key,
                language=resolve_book_language(
                    book,
                    requested_language=normalized_language,
                    has_translation=translation is not None,
                ),
                published=book.published,
                publication_status=book.publication_status,
                page_count=page_count_lookup.get(book.id, 0),
                audio_available=book.audio_available,
            )
        )
    return summaries
