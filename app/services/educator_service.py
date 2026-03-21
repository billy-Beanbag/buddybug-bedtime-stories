from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, ClassroomSet, ClassroomSetItem, User
from app.schemas.discovery_schema import DiscoverySearchResult
from app.schemas.educator_schema import (
    ClassroomSetCreate,
    ClassroomSetDetailResponse,
    ClassroomSetItemCreate,
    ClassroomSetItemRead,
    ClassroomSetRead,
    ClassroomSetUpdate,
)
from app.services.discovery_service import _display_title, _ensure_metadata_for_books, _score_result
from app.services.i18n_service import validate_language_code
from app.services.review_service import utc_now


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _validate_age_band(age_band: str | None) -> str | None:
    if age_band is None:
        return None
    if age_band not in {"3-7", "8-12"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported age band")
    return age_band


def get_classroom_set_or_404(session: Session, *, set_id: int) -> ClassroomSet:
    classroom_set = session.get(ClassroomSet, set_id)
    if classroom_set is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom set not found")
    return classroom_set


def get_classroom_set_item_or_404(session: Session, *, item_id: int) -> ClassroomSetItem:
    item = session.get(ClassroomSetItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom set item not found")
    return item


def validate_educator_ownership(*, current_user: User, classroom_set: ClassroomSet) -> None:
    if current_user.is_admin:
        return
    if classroom_set.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this classroom set")


def list_classroom_sets_for_educator(session: Session, *, current_user: User) -> list[ClassroomSet]:
    statement = select(ClassroomSet).order_by(ClassroomSet.updated_at.desc(), ClassroomSet.title.asc())
    if not current_user.is_admin:
        statement = statement.where(ClassroomSet.user_id == current_user.id)
    return list(session.exec(statement).all())


def create_classroom_set(session: Session, *, current_user: User, payload: ClassroomSetCreate) -> ClassroomSet:
    classroom_set = ClassroomSet(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        age_band=_validate_age_band(payload.age_band),
        language=validate_language_code(payload.language) if payload.language is not None else None,
        is_active=payload.is_active,
    )
    return _persist(session, classroom_set)


def update_classroom_set(
    session: Session,
    *,
    classroom_set: ClassroomSet,
    payload: ClassroomSetUpdate,
) -> ClassroomSet:
    update_data = payload.model_dump(exclude_unset=True)
    if "age_band" in update_data:
        update_data["age_band"] = _validate_age_band(update_data["age_band"])
    if "language" in update_data and update_data["language"] is not None:
        update_data["language"] = validate_language_code(update_data["language"])
    for field_name, value in update_data.items():
        setattr(classroom_set, field_name, value)
    classroom_set.updated_at = utc_now()
    return _persist(session, classroom_set)


def delete_classroom_set(session: Session, *, classroom_set: ClassroomSet) -> None:
    items = list(session.exec(select(ClassroomSetItem).where(ClassroomSetItem.classroom_set_id == classroom_set.id)).all())
    for item in items:
        session.delete(item)
    session.delete(classroom_set)
    session.commit()


def add_classroom_set_item(
    session: Session,
    *,
    classroom_set: ClassroomSet,
    payload: ClassroomSetItemCreate,
) -> ClassroomSetItem:
    book = session.get(Book, payload.book_id)
    if book is None or not book.published or book.publication_status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published book not found")
    existing = session.exec(
        select(ClassroomSetItem).where(
            ClassroomSetItem.classroom_set_id == classroom_set.id,
            ClassroomSetItem.book_id == payload.book_id,
        )
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is already in this classroom set")
    item = ClassroomSetItem(
        classroom_set_id=classroom_set.id,
        book_id=payload.book_id,
        position=payload.position,
    )
    return _persist(session, item)


def remove_classroom_set_item(session: Session, *, item: ClassroomSetItem) -> None:
    session.delete(item)
    session.commit()


def get_classroom_set_detail(
    session: Session,
    *,
    classroom_set: ClassroomSet,
) -> ClassroomSetDetailResponse:
    set_items = list(
        session.exec(
            select(ClassroomSetItem)
            .where(ClassroomSetItem.classroom_set_id == classroom_set.id)
            .order_by(ClassroomSetItem.position.asc(), ClassroomSetItem.created_at.asc())
        ).all()
    )
    books = [session.get(Book, item.book_id) for item in set_items]
    books = [book for book in books if book is not None and book.published and book.publication_status == "published"]
    metadata_by_book_id = _ensure_metadata_for_books(session, books=books)
    results_by_book_id: dict[int, DiscoverySearchResult] = {}
    requested_language = classroom_set.language
    for book in books:
        metadata = metadata_by_book_id[book.id]
        score, reasons = _score_result(
            metadata=metadata,
            book=book,
            query=None,
            requested_language=requested_language,
            bedtime_bias=False,
            base_reasons=["classroom set"],
        )
        results_by_book_id[book.id] = DiscoverySearchResult(
            book_id=book.id,
            title=_display_title(session, book=book, requested_language=requested_language),
            cover_image_url=book.cover_image_url,
            age_band=book.age_band,
            language=book.language,
            content_lane_key=book.content_lane_key,
            published=book.published,
            publication_status=book.publication_status,
            score=round(score, 2),
            reasons=reasons,
        )
    ordered_items = [results_by_book_id[item.book_id] for item in set_items if item.book_id in results_by_book_id]
    return ClassroomSetDetailResponse(
        classroom_set=ClassroomSetRead.model_validate(classroom_set),
        set_items=[ClassroomSetItemRead.model_validate(item) for item in set_items],
        items=ordered_items,
    )
