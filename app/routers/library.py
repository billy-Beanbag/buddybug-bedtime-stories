from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.library_schema import (
    BookDownloadPackageRead,
    BookPackageGenerateRequest,
    BookPackageGenerateResponse,
    ReaderDownloadAccessResponse,
    SavedLibraryResponse,
    UserLibraryItemCreate,
    UserLibraryItemRead,
    UserLibraryItemUpdate,
)
from app.services.achievement_service import handle_story_saved
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.library_service import (
    archive_library_item,
    build_book_download_package,
    get_download_access_for_user,
    get_library_item,
    get_library_items_for_user,
    list_packages_for_book,
    mark_library_item_opened,
    mark_package_downloaded,
    remove_library_item,
    update_library_item,
    upsert_library_item,
    validate_child_profile_for_user,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/library", tags=["library"])
admin_router = APIRouter(prefix="/admin/library", tags=["admin-library"])


@router.get("/me", response_model=SavedLibraryResponse, summary="List the current user's saved library")
def get_my_library(
    child_profile_id: int | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    saved_for_offline: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SavedLibraryResponse:
    validate_child_profile_for_user(session, user=current_user, child_profile_id=child_profile_id)
    items = get_library_items_for_user(
        session,
        user_id=current_user.id,
        child_profile_id=child_profile_id,
        status_value=status_value,
        saved_for_offline=saved_for_offline,
        limit=limit,
    )
    return SavedLibraryResponse(items=[UserLibraryItemRead.model_validate(item) for item in items])


@router.post("/me", response_model=UserLibraryItemRead, summary="Save a book to the current user's library")
def save_book_to_library(
    payload: UserLibraryItemCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserLibraryItemRead:
    item = upsert_library_item(
        session,
        user=current_user,
        book_id=payload.book_id,
        child_profile_id=payload.child_profile_id,
        saved_for_offline=payload.saved_for_offline,
        status_value="saved",
    )
    track_event_safe(
        session,
        event_name="book_saved",
        user=current_user,
        child_profile_id=payload.child_profile_id,
        book_id=payload.book_id,
        metadata={"saved_for_offline": payload.saved_for_offline},
    )
    if payload.saved_for_offline:
        track_event_safe(
            session,
            event_name="offline_marked",
            user=current_user,
            child_profile_id=payload.child_profile_id,
            book_id=payload.book_id,
            metadata={"source": "library_save"},
        )
    handle_story_saved(
        session,
        user=current_user,
        child_profile_id=payload.child_profile_id,
        source_table="userlibraryitem",
        source_id=str(item.id),
    )
    return item


@router.patch("/me/books/{book_id}", response_model=UserLibraryItemRead, summary="Update one library item")
def patch_library_item(
    book_id: int,
    payload: UserLibraryItemUpdate,
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserLibraryItemRead:
    validate_child_profile_for_user(session, user=current_user, child_profile_id=child_profile_id)
    item = get_library_item(session, user_id=current_user.id, book_id=book_id, child_profile_id=child_profile_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library item not found")
    updated = update_library_item(
        session,
        library_item=item,
        status_value=payload.status,
        saved_for_offline=payload.saved_for_offline,
        last_opened_at=payload.last_opened_at,
        downloaded_at=payload.downloaded_at,
    )
    if payload.saved_for_offline:
        track_event_safe(
            session,
            event_name="offline_marked",
            user=current_user,
            child_profile_id=child_profile_id,
            book_id=book_id,
            metadata={"source": "library_patch"},
        )
    return updated


@router.post(
    "/me/books/{book_id}/archive",
    response_model=UserLibraryItemRead,
    summary="Archive one saved library item",
)
def archive_my_library_item(
    book_id: int,
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserLibraryItemRead:
    validate_child_profile_for_user(session, user=current_user, child_profile_id=child_profile_id)
    item = archive_library_item(
        session,
        user=current_user,
        book_id=book_id,
        child_profile_id=child_profile_id,
    )
    track_event_safe(
        session,
        event_name="book_archived",
        user=current_user,
        child_profile_id=child_profile_id,
        book_id=book_id,
        metadata={"source": "library_archive"},
    )
    return item


@router.delete("/me/books/{book_id}", response_model=UserLibraryItemRead, summary="Remove one library item")
def delete_my_library_item(
    book_id: int,
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserLibraryItemRead:
    validate_child_profile_for_user(session, user=current_user, child_profile_id=child_profile_id)
    return remove_library_item(
        session,
        user=current_user,
        book_id=book_id,
        child_profile_id=child_profile_id,
    )


@router.post(
    "/me/books/{book_id}/opened",
    response_model=UserLibraryItemRead | None,
    summary="Update last opened timestamp for a library item if present",
)
def mark_book_opened_in_library(
    book_id: int,
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserLibraryItemRead | None:
    validate_child_profile_for_user(session, user=current_user, child_profile_id=child_profile_id)
    item = mark_library_item_opened(
        session,
        user=current_user,
        book_id=book_id,
        child_profile_id=child_profile_id,
    )
    return UserLibraryItemRead.model_validate(item) if item is not None else None


@router.get(
    "/me/books/{book_id}/download-access",
    response_model=ReaderDownloadAccessResponse,
    summary="Get download entitlement for one book",
)
def get_my_download_access(
    book_id: int,
    language: str = Query(default="en"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReaderDownloadAccessResponse:
    return get_download_access_for_user(session, user=current_user, book_id=book_id, language=language)


@router.post(
    "/me/books/{book_id}/download",
    response_model=BookDownloadPackageRead,
    summary="Generate or return a downloadable book package",
)
def download_my_book_package(
    book_id: int,
    language: str = Query(default="en"),
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BookDownloadPackageRead:
    validate_child_profile_for_user(session, user=current_user, child_profile_id=child_profile_id)
    access = get_download_access_for_user(session, user=current_user, book_id=book_id, language=language)
    if not access.can_download_full_book:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=access.reason)
    track_event_safe(
        session,
        event_name="download_started",
        user=current_user,
        child_profile_id=child_profile_id,
        book_id=book_id,
        language=language,
        metadata={"source": "library_download"},
    )
    package = build_book_download_package(
        session,
        book_id=book_id,
        language=language,
        replace_existing=False,
    )
    mark_package_downloaded(
        session,
        user=current_user,
        book_id=book_id,
        child_profile_id=child_profile_id,
    )
    track_event_safe(
        session,
        event_name="download_completed",
        user=current_user,
        child_profile_id=child_profile_id,
        book_id=book_id,
        language=language,
        metadata={"package_url": package.package_url},
    )
    return package


@admin_router.post(
    "/books/{book_id}/packages/generate",
    response_model=BookPackageGenerateResponse,
    summary="Generate or regenerate a book download package",
)
def generate_book_package(
    book_id: int,
    payload: BookPackageGenerateRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> BookPackageGenerateResponse:
    if payload.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="book_id mismatch")
    had_existing = bool(list_packages_for_book(session, book_id=book_id, language=payload.language))
    package = build_book_download_package(
        session,
        book_id=book_id,
        language=payload.language,
        replace_existing=payload.replace_existing,
    )
    create_audit_log(
        session,
        action_type="book_download_package_regenerated" if had_existing and payload.replace_existing else "book_download_package_generated",
        entity_type="book_download_package",
        entity_id=str(package.id),
        summary=f"Generated download package for book {book_id} ({package.language})",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": book_id, "language": package.language, "package_version": package.package_version},
    )
    return BookPackageGenerateResponse(package=BookDownloadPackageRead.model_validate(package))


@admin_router.get(
    "/books/{book_id}/packages",
    response_model=list[BookDownloadPackageRead],
    summary="List package records for one book",
)
def get_book_packages(
    book_id: int,
    language: str | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[BookDownloadPackageRead]:
    packages = list_packages_for_book(session, book_id=book_id, language=language)
    return [BookDownloadPackageRead.model_validate(package) for package in packages]
