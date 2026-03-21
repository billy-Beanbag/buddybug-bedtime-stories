from __future__ import annotations

import json

from fastapi import HTTPException, status
from sqlmodel import Session, desc, select

from app.models import (
    Book,
    BookAudio,
    BookDownloadPackage,
    BookNarration,
    ChildProfile,
    NarrationSegment,
    NarrationVoice,
    User,
    UserLibraryItem,
)
from app.schemas.library_schema import ReaderDownloadAccessResponse
from app.services.audio_service import get_book_audio_or_404
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.i18n_service import get_localized_book_detail, normalize_language
from app.services.reader_service import get_published_book_or_404
from app.services.review_service import utc_now
from app.services.storage_service import build_mock_download_package_path, get_asset_url, save_bytes
from app.services.subscription_service import has_premium_access

ALLOWED_LIBRARY_ITEM_STATUSES = {"saved", "archived", "removed"}
ALLOWED_PACKAGE_FORMATS = {"json_bundle"}


def validate_library_item_status(status_value: str) -> str:
    if status_value not in ALLOWED_LIBRARY_ITEM_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid library item status")
    return status_value


def validate_package_format(package_format: str) -> str:
    if package_format not in ALLOWED_PACKAGE_FORMATS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid package format")
    return package_format


def validate_child_profile_for_user(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None,
) -> ChildProfile | None:
    return validate_child_profile_ownership(session, user_id=user.id, child_profile_id=child_profile_id)


def get_library_item(
    session: Session,
    *,
    user_id: int,
    book_id: int,
    child_profile_id: int | None = None,
) -> UserLibraryItem | None:
    statement = select(UserLibraryItem).where(
        UserLibraryItem.user_id == user_id,
        UserLibraryItem.book_id == book_id,
    )
    if child_profile_id is None:
        statement = statement.where(UserLibraryItem.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(UserLibraryItem.child_profile_id == child_profile_id)
    return session.exec(statement.order_by(desc(UserLibraryItem.updated_at))).first()


def get_library_items_for_user(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None = None,
    status_value: str | None = None,
    saved_for_offline: bool | None = None,
    limit: int = 100,
) -> list[UserLibraryItem]:
    statement = (
        select(UserLibraryItem)
        .where(UserLibraryItem.user_id == user_id)
        .order_by(desc(UserLibraryItem.updated_at), desc(UserLibraryItem.created_at))
        .limit(limit)
    )
    if child_profile_id is not None:
        statement = statement.where(UserLibraryItem.child_profile_id == child_profile_id)
    if status_value is not None:
        statement = statement.where(UserLibraryItem.status == validate_library_item_status(status_value))
    else:
        statement = statement.where(UserLibraryItem.status != "removed")
    if saved_for_offline is not None:
        statement = statement.where(UserLibraryItem.saved_for_offline == saved_for_offline)
    return list(session.exec(statement).all())


def upsert_library_item(
    session: Session,
    *,
    user: User,
    book_id: int,
    child_profile_id: int | None = None,
    saved_for_offline: bool = False,
    status_value: str = "saved",
) -> UserLibraryItem:
    get_published_book_or_404(session, book_id)
    child_profile = validate_child_profile_for_user(
        session,
        user=user,
        child_profile_id=child_profile_id,
    )
    existing = get_library_item(
        session,
        user_id=user.id,
        book_id=book_id,
        child_profile_id=child_profile.id if child_profile is not None else None,
    )
    if existing is None:
        existing = UserLibraryItem(
            user_id=user.id,
            child_profile_id=child_profile.id if child_profile is not None else None,
            book_id=book_id,
            status=validate_library_item_status(status_value),
            saved_for_offline=saved_for_offline,
        )
    else:
        existing.status = validate_library_item_status(status_value)
        existing.saved_for_offline = saved_for_offline
        existing.updated_at = utc_now()
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


def update_library_item(
    session: Session,
    *,
    library_item: UserLibraryItem,
    status_value: str | None = None,
    saved_for_offline: bool | None = None,
    last_opened_at=None,
    downloaded_at=None,
) -> UserLibraryItem:
    if status_value is not None:
        library_item.status = validate_library_item_status(status_value)
    if saved_for_offline is not None:
        library_item.saved_for_offline = saved_for_offline
    if last_opened_at is not None:
        library_item.last_opened_at = last_opened_at
    if downloaded_at is not None:
        library_item.downloaded_at = downloaded_at
    library_item.updated_at = utc_now()
    session.add(library_item)
    session.commit()
    session.refresh(library_item)
    return library_item


def archive_library_item(
    session: Session,
    *,
    user: User,
    book_id: int,
    child_profile_id: int | None = None,
) -> UserLibraryItem:
    item = get_library_item(session, user_id=user.id, book_id=book_id, child_profile_id=child_profile_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library item not found")
    return update_library_item(session, library_item=item, status_value="archived")


def remove_library_item(
    session: Session,
    *,
    user: User,
    book_id: int,
    child_profile_id: int | None = None,
) -> UserLibraryItem:
    item = get_library_item(session, user_id=user.id, book_id=book_id, child_profile_id=child_profile_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library item not found")
    return update_library_item(
        session,
        library_item=item,
        status_value="removed",
        saved_for_offline=False,
    )


def mark_library_item_opened(
    session: Session,
    *,
    user: User,
    book_id: int,
    child_profile_id: int | None = None,
) -> UserLibraryItem | None:
    item = get_library_item(session, user_id=user.id, book_id=book_id, child_profile_id=child_profile_id)
    if item is None:
        return None
    return update_library_item(session, library_item=item, last_opened_at=utc_now())


def get_active_package_for_book(session: Session, *, book_id: int, language: str) -> BookDownloadPackage | None:
    normalized_language = normalize_language(language)
    statement = (
        select(BookDownloadPackage)
        .where(
            BookDownloadPackage.book_id == book_id,
            BookDownloadPackage.language == normalized_language,
            BookDownloadPackage.is_active.is_(True),
        )
        .order_by(desc(BookDownloadPackage.package_version), desc(BookDownloadPackage.updated_at))
    )
    return session.exec(statement).first()


def list_packages_for_book(session: Session, *, book_id: int, language: str | None = None) -> list[BookDownloadPackage]:
    statement = (
        select(BookDownloadPackage)
        .where(BookDownloadPackage.book_id == book_id)
        .order_by(desc(BookDownloadPackage.package_version), desc(BookDownloadPackage.updated_at))
    )
    if language is not None:
        statement = statement.where(BookDownloadPackage.language == normalize_language(language))
    return list(session.exec(statement).all())


def _next_package_version(session: Session, *, book_id: int, language: str) -> int:
    latest = session.exec(
        select(BookDownloadPackage)
        .where(BookDownloadPackage.book_id == book_id, BookDownloadPackage.language == language)
        .order_by(desc(BookDownloadPackage.package_version))
    ).first()
    return 1 if latest is None else latest.package_version + 1


def _active_audio_payload(session: Session, *, book_id: int) -> list[dict[str, object]]:
    rows = list(
        session.exec(
            select(BookAudio).where(
                BookAudio.book_id == book_id,
                BookAudio.approval_status == "approved",
                BookAudio.is_active.is_(True),
            )
        ).all()
    )
    payload: list[dict[str, object]] = []
    for row in rows:
        try:
            audio = get_book_audio_or_404(session, row.id)
        except HTTPException:
            continue
        payload.append(
            {
                "id": audio.id,
                "voice_id": audio.voice_id,
                "audio_url": audio.audio_url,
                "duration_seconds": audio.duration_seconds,
                "version_number": audio.version_number,
            }
        )
    return payload


def _active_narration_payload(
    session: Session,
    *,
    book_id: int,
    language: str,
) -> dict[str, object] | None:
    narration = session.exec(
        select(BookNarration)
        .where(
            BookNarration.book_id == book_id,
            BookNarration.language == language,
            BookNarration.is_active.is_(True),
        )
        .order_by(BookNarration.updated_at.desc(), BookNarration.id.desc())
    ).first()
    if narration is None:
        return None
    voice = session.get(NarrationVoice, narration.narration_voice_id)
    if voice is None:
        return None
    segments = list(
        session.exec(
            select(NarrationSegment)
            .where(NarrationSegment.narration_id == narration.id)
            .order_by(NarrationSegment.page_number.asc())
        ).all()
    )
    return {
        "narration_id": narration.id,
        "voice_key": voice.key,
        "voice_display_name": voice.display_name,
        "language": narration.language,
        "duration_seconds": narration.duration_seconds,
        "segments": [
            {
                "page_number": segment.page_number,
                "audio_url": segment.audio_url,
                "duration_seconds": segment.duration_seconds,
            }
            for segment in segments
        ],
    }


def build_book_download_package(
    session: Session,
    *,
    book_id: int,
    language: str = "en",
    replace_existing: bool = True,
) -> BookDownloadPackage:
    book = get_published_book_or_404(session, book_id)
    normalized_language = normalize_language(language)
    existing = get_active_package_for_book(session, book_id=book.id, language=normalized_language)
    if existing is not None and not replace_existing:
        return existing

    if existing is not None:
        existing.is_active = False
        existing.updated_at = utc_now()
        session.add(existing)
        session.commit()

    package_version = _next_package_version(session, book_id=book.id, language=normalized_language)
    detail = get_localized_book_detail(
        session,
        book.id,
        requested_language=normalized_language,
        current_user=None,
        apply_access_control=False,
    )
    package_payload = {
        "book": {
            "book_id": detail.book_id,
            "title": detail.title,
            "cover_image_url": detail.cover_image_url,
            "age_band": detail.age_band,
            "content_lane_key": detail.content_lane_key,
            "language": detail.language,
            "published": detail.published,
            "publication_status": detail.publication_status,
        },
        "pages": [page.model_dump() for page in detail.pages],
        "legacy_audio": _active_audio_payload(session, book_id=book.id),
        "audio": _active_narration_payload(session, book_id=book.id, language=detail.language),
        "language": detail.language,
        "package_version": package_version,
    }
    asset_path = save_bytes(
        build_mock_download_package_path(
            book_id=book.id,
            language=normalized_language,
            version_number=package_version,
        ),
        json.dumps(package_payload, ensure_ascii=True, sort_keys=True).encode("utf-8"),
    )
    package = BookDownloadPackage(
        book_id=book.id,
        language=detail.language,
        package_version=package_version,
        package_url=get_asset_url(asset_path),
        package_format=validate_package_format("json_bundle"),
        is_active=True,
    )
    session.add(package)
    session.commit()
    session.refresh(package)
    return package


def get_download_access_for_user(
    session: Session,
    *,
    user: User,
    book_id: int,
    language: str = "en",
) -> ReaderDownloadAccessResponse:
    book = get_published_book_or_404(session, book_id)
    package = get_active_package_for_book(session, book_id=book.id, language=language)
    if user.is_admin or has_premium_access(user):
        return ReaderDownloadAccessResponse(
            book_id=book.id,
            can_download_full_book=True,
            package_available=package is not None,
            package_url=package.package_url if package is not None else None,
            reason="Premium download available",
        )
    return ReaderDownloadAccessResponse(
        book_id=book.id,
        can_download_full_book=False,
        package_available=False,
        package_url=None,
        reason="Premium subscription required for offline download packages",
    )


def mark_package_downloaded(
    session: Session,
    *,
    user: User,
    book_id: int,
    child_profile_id: int | None = None,
) -> UserLibraryItem | None:
    item = get_library_item(session, user_id=user.id, book_id=book_id, child_profile_id=child_profile_id)
    if item is None:
        return None
    return update_library_item(
        session,
        library_item=item,
        downloaded_at=utc_now(),
        saved_for_offline=True,
    )
