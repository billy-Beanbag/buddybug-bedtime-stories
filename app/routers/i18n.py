from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Book, BookPage, BookPageTranslation, BookTranslation, User
from app.schemas.i18n_schema import (
    BookPageTranslationCreate,
    BookPageTranslationRead,
    BookPageTranslationUpdate,
    BookTranslationCreate,
    BookTranslationRead,
    BookTranslationUpdate,
    CloneBookToLanguageRequest,
)
from app.services.i18n_service import clone_book_to_language, upsert_book_page_translation, upsert_book_translation, validate_language_code
from app.services.review_service import utc_now
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/i18n", tags=["i18n"])


def _get_book_or_404(session: Session, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


def _get_book_page_or_404(session: Session, book_page_id: int) -> BookPage:
    book_page = session.get(BookPage, book_page_id)
    if book_page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book page not found")
    return book_page


def _get_book_translation_or_404(session: Session, translation_id: int) -> BookTranslation:
    translation = session.get(BookTranslation, translation_id)
    if translation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book translation not found")
    return translation


def _get_book_page_translation_or_404(session: Session, translation_id: int) -> BookPageTranslation:
    translation = session.get(BookPageTranslation, translation_id)
    if translation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book page translation not found")
    return translation


@router.get("/books/{book_id}/translations", response_model=list[BookTranslationRead], summary="List translations for a book")
def list_book_translations(
    book_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[BookTranslation]:
    _get_book_or_404(session, book_id)
    return list(
        session.exec(
            select(BookTranslation).where(BookTranslation.book_id == book_id).order_by(BookTranslation.language)
        ).all()
    )


@router.post(
    "/books/{book_id}/translations",
    response_model=BookTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create or replace a book translation",
)
def create_book_translation(
    book_id: int,
    payload: BookTranslationCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> BookTranslation:
    if payload.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="book_id must match route")
    return upsert_book_translation(
        session,
        book_id=book_id,
        language=payload.language,
        title=payload.title,
        description=payload.description,
        published=payload.published,
    )


@router.patch(
    "/book-translations/{translation_id}",
    response_model=BookTranslationRead,
    summary="Update a book translation",
)
def update_book_translation(
    translation_id: int,
    payload: BookTranslationUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> BookTranslation:
    translation = _get_book_translation_or_404(session, translation_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "language" in update_data and update_data["language"] is not None:
        target_language = validate_language_code(update_data["language"])
        existing = session.exec(
            select(BookTranslation).where(
                BookTranslation.book_id == translation.book_id,
                BookTranslation.language == target_language,
            )
        ).first()
        if existing is not None and existing.id != translation.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Translation already exists for language")
        translation.language = target_language
    if "title" in update_data and update_data["title"] is not None:
        translation.title = update_data["title"]
    if "description" in update_data:
        translation.description = update_data["description"]
    if "published" in update_data and update_data["published"] is not None:
        translation.published = update_data["published"]
    translation.updated_at = utc_now()
    session.add(translation)
    session.commit()
    session.refresh(translation)
    return translation


@router.delete("/book-translations/{translation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a book translation")
def delete_book_translation(
    translation_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Response:
    translation = _get_book_translation_or_404(session, translation_id)
    session.delete(translation)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/books/{book_id}/page-translations",
    response_model=list[BookPageTranslationRead],
    summary="List all page translations for a book",
)
def list_book_page_translations(
    book_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[BookPageTranslation]:
    _get_book_or_404(session, book_id)
    page_ids = list(session.exec(select(BookPage.id).where(BookPage.book_id == book_id)).all())
    if not page_ids:
        return []
    return list(
        session.exec(
            select(BookPageTranslation)
            .where(BookPageTranslation.book_page_id.in_(page_ids))
            .order_by(BookPageTranslation.language, BookPageTranslation.book_page_id)
        ).all()
    )


@router.post(
    "/book-pages/{book_page_id}/translations",
    response_model=BookPageTranslationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create or replace a book page translation",
)
def create_book_page_translation(
    book_page_id: int,
    payload: BookPageTranslationCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> BookPageTranslation:
    if payload.book_page_id != book_page_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="book_page_id must match route")
    _get_book_page_or_404(session, book_page_id)
    return upsert_book_page_translation(
        session,
        book_page_id=book_page_id,
        language=payload.language,
        text_content=payload.text_content,
    )


@router.patch(
    "/book-page-translations/{translation_id}",
    response_model=BookPageTranslationRead,
    summary="Update a book page translation",
)
def update_book_page_translation(
    translation_id: int,
    payload: BookPageTranslationUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> BookPageTranslation:
    translation = _get_book_page_translation_or_404(session, translation_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "language" in update_data and update_data["language"] is not None:
        target_language = validate_language_code(update_data["language"])
        existing = session.exec(
            select(BookPageTranslation).where(
                BookPageTranslation.book_page_id == translation.book_page_id,
                BookPageTranslation.language == target_language,
            )
        ).first()
        if existing is not None and existing.id != translation.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page translation already exists for language")
        translation.language = target_language
    if "text_content" in update_data and update_data["text_content"] is not None:
        translation.text_content = update_data["text_content"]
    translation.updated_at = utc_now()
    session.add(translation)
    session.commit()
    session.refresh(translation)
    return translation


@router.delete(
    "/book-page-translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book page translation",
)
def delete_book_page_translation(
    translation_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Response:
    translation = _get_book_page_translation_or_404(session, translation_id)
    session.delete(translation)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/books/{book_id}/clone-to-language",
    response_model=BookTranslationRead,
    summary="Clone original book content into placeholder translations for a target language",
)
def clone_translation_placeholders(
    book_id: int,
    payload: CloneBookToLanguageRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> BookTranslation:
    book = _get_book_or_404(session, book_id)
    translation, _ = clone_book_to_language(session, book=book, language=payload.language)
    return translation
