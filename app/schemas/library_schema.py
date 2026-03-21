from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserLibraryItemCreate(BaseModel):
    book_id: int
    child_profile_id: int | None = None
    saved_for_offline: bool = False


class UserLibraryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    child_profile_id: int | None = None
    book_id: int
    status: str
    saved_for_offline: bool
    last_opened_at: datetime | None = None
    downloaded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserLibraryItemUpdate(BaseModel):
    status: str | None = None
    saved_for_offline: bool | None = None
    last_opened_at: datetime | None = None
    downloaded_at: datetime | None = None


class BookDownloadPackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    language: str
    package_version: int
    package_url: str
    package_format: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SavedLibraryResponse(BaseModel):
    items: list[UserLibraryItemRead]


class BookPackageGenerateRequest(BaseModel):
    book_id: int
    language: str = "en"
    replace_existing: bool = True


class BookPackageGenerateResponse(BaseModel):
    package: BookDownloadPackageRead


class ReaderDownloadAccessResponse(BaseModel):
    book_id: int
    can_download_full_book: bool
    package_available: bool
    package_url: str | None = None
    reason: str
