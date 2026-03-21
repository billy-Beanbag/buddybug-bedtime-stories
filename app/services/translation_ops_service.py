from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, BookPage, BookPageTranslation, BookTranslation, TranslationTask, User
from app.schemas.translation_ops_schema import TranslationTaskDetailResponse, TranslationTaskUpdate
from app.services.i18n_service import SUPPORTED_LANGUAGE_CODES, validate_language_code
from app.services.review_service import utc_now

TRANSLATION_TASK_STATUSES = {
    "not_started",
    "in_progress",
    "in_review",
    "completed",
    "blocked",
}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_translation_task_status(status_value: str) -> str:
    if status_value not in TRANSLATION_TASK_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid translation task status")
    return status_value


def get_translation_task_or_404(session: Session, task_id: int) -> TranslationTask:
    task = session.get(TranslationTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation task not found")
    return task


def _get_book_or_404(session: Session, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


def _count_book_pages(session: Session, *, book_id: int) -> int:
    return len(list(session.exec(select(BookPage.id).where(BookPage.book_id == book_id)).all()))


def _count_page_translations(session: Session, *, book_id: int, language: str) -> int:
    page_ids = list(session.exec(select(BookPage.id).where(BookPage.book_id == book_id)).all())
    if not page_ids:
        return 0
    return len(
        list(
            session.exec(
                select(BookPageTranslation.id).where(
                    BookPageTranslation.book_page_id.in_(page_ids),
                    BookPageTranslation.language == language,
                )
            ).all()
        )
    )


def _get_book_translation(session: Session, *, book_id: int, language: str) -> BookTranslation | None:
    return session.exec(
        select(BookTranslation).where(BookTranslation.book_id == book_id, BookTranslation.language == language)
    ).first()


def _build_translation_detail(
    session: Session,
    *,
    book: Book,
    language: str,
    task: TranslationTask | None,
) -> TranslationTaskDetailResponse:
    book_translation = _get_book_translation(session, book_id=book.id, language=language)
    total_page_count = _count_book_pages(session, book_id=book.id)
    translated_page_count = _count_page_translations(session, book_id=book.id, language=language)
    is_complete = book_translation is not None and translated_page_count >= total_page_count
    return TranslationTaskDetailResponse(
        task=task,
        book_id=book.id,
        book_title=book.title,
        age_band=book.age_band,
        source_language=book.language,
        target_language=language,
        has_book_translation=book_translation is not None,
        translated_page_count=translated_page_count,
        total_page_count=total_page_count,
        missing_page_count=max(total_page_count - translated_page_count, 0),
        is_translation_complete=is_complete,
        is_translation_published=bool(book_translation is not None and book_translation.published),
    )


def _sync_task_completion(session: Session, *, task: TranslationTask) -> TranslationTask:
    book = _get_book_or_404(session, task.book_id)
    detail = _build_translation_detail(session, book=book, language=task.language, task=task)
    if detail.is_translation_complete and task.status != "completed":
        task.status = "completed"
        task.completed_at = utc_now()
        task.updated_at = utc_now()
        return _persist(session, task)
    if not detail.is_translation_complete and task.status == "completed":
        task.completed_at = None
        task.updated_at = utc_now()
        return _persist(session, task)
    return task


def create_translation_task(
    session: Session,
    *,
    book_id: int,
    language: str,
    status_value: str,
    assigned_to_user_id: int | None,
    source_version_label: str | None,
    notes: str | None,
    due_at,
) -> TranslationTask:
    book = _get_book_or_404(session, book_id)
    normalized_language = validate_language_code(language)
    if normalized_language == book.language:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target language must differ from the book source language")
    existing = session.exec(
        select(TranslationTask).where(TranslationTask.book_id == book_id, TranslationTask.language == normalized_language)
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Translation task already exists for this book and language")
    if assigned_to_user_id is not None and session.get(User, assigned_to_user_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user not found")
    task = TranslationTask(
        book_id=book_id,
        language=normalized_language,
        status=validate_translation_task_status(status_value),
        assigned_to_user_id=assigned_to_user_id,
        source_version_label=source_version_label,
        notes=notes,
        due_at=due_at,
    )
    task = _persist(session, task)
    return _sync_task_completion(session, task=task)


def update_translation_task(
    session: Session,
    *,
    task: TranslationTask,
    payload: TranslationTaskUpdate,
) -> TranslationTask:
    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        task.status = validate_translation_task_status(update_data["status"])
    if "assigned_to_user_id" in update_data:
        if update_data["assigned_to_user_id"] is not None and session.get(User, update_data["assigned_to_user_id"]) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user not found")
        task.assigned_to_user_id = update_data["assigned_to_user_id"]
    if "source_version_label" in update_data:
        task.source_version_label = update_data["source_version_label"]
    if "notes" in update_data:
        task.notes = update_data["notes"]
    if "due_at" in update_data:
        task.due_at = update_data["due_at"]
    if "completed_at" in update_data:
        task.completed_at = update_data["completed_at"]
    if task.status == "completed" and task.completed_at is None:
        task.completed_at = utc_now()
    if task.status != "completed" and "completed_at" not in update_data:
        task.completed_at = None
    task.updated_at = utc_now()
    task = _persist(session, task)
    return _sync_task_completion(session, task=task)


def list_translation_tasks(
    session: Session,
    *,
    language: str | None,
    status_value: str | None,
    assigned_to_user_id: int | None,
    limit: int,
) -> list[TranslationTaskDetailResponse]:
    statement = select(TranslationTask).order_by(TranslationTask.updated_at.desc()).limit(limit)
    if language is not None:
        statement = statement.where(TranslationTask.language == validate_language_code(language))
    if status_value is not None:
        statement = statement.where(TranslationTask.status == validate_translation_task_status(status_value))
    if assigned_to_user_id is not None:
        statement = statement.where(TranslationTask.assigned_to_user_id == assigned_to_user_id)
    tasks = list(session.exec(statement).all())
    details: list[TranslationTaskDetailResponse] = []
    for task in tasks:
        synced_task = _sync_task_completion(session, task=task)
        details.append(_build_translation_detail(session, book=_get_book_or_404(session, synced_task.book_id), language=synced_task.language, task=synced_task))
    return details


def get_translation_task_detail(session: Session, *, task_id: int) -> TranslationTaskDetailResponse:
    task = _sync_task_completion(session, task=get_translation_task_or_404(session, task_id))
    return _build_translation_detail(session, book=_get_book_or_404(session, task.book_id), language=task.language, task=task)


def infer_missing_translations(
    session: Session,
    *,
    language: str | None,
    age_band: str | None,
    limit: int,
) -> list[TranslationTaskDetailResponse]:
    statement = select(Book).where(Book.published.is_(True), Book.publication_status == "published").order_by(Book.updated_at.desc())
    if age_band is not None:
        statement = statement.where(Book.age_band == age_band)
    books = list(session.exec(statement).all())
    items: list[TranslationTaskDetailResponse] = []
    target_languages = [validate_language_code(language)] if language is not None else None
    for book in books:
        languages = target_languages or [code for code in SUPPORTED_LANGUAGE_CODES if code != book.language]
        for target_language in languages:
            if target_language == book.language:
                continue
            task = session.exec(
                select(TranslationTask).where(TranslationTask.book_id == book.id, TranslationTask.language == target_language)
            ).first()
            detail = _build_translation_detail(session, book=book, language=target_language, task=task)
            if detail.is_translation_complete:
                if task is not None:
                    _sync_task_completion(session, task=task)
                continue
            items.append(detail)
            if len(items) >= limit:
                return items
    return items
