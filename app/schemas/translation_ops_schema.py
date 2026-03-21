from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TranslationTaskCreate(BaseModel):
    book_id: int
    language: str
    status: str = "not_started"
    assigned_to_user_id: int | None = None
    source_version_label: str | None = None
    notes: str | None = None
    due_at: datetime | None = None


class TranslationTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    language: str
    status: str
    assigned_to_user_id: int | None = None
    source_version_label: str | None = None
    notes: str | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TranslationTaskUpdate(BaseModel):
    status: str | None = None
    assigned_to_user_id: int | None = None
    source_version_label: str | None = None
    notes: str | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None


class TranslationTaskDetailResponse(BaseModel):
    task: TranslationTaskRead | None = None
    book_id: int
    book_title: str
    age_band: str
    source_language: str
    target_language: str
    has_book_translation: bool
    translated_page_count: int
    total_page_count: int
    missing_page_count: int
    is_translation_complete: bool
    is_translation_published: bool
