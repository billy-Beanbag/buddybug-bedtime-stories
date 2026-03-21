from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.book_schema import BookPageRead, BookRead
from app.schemas.quality_schema import QualityCheckRead
from app.schemas.story_schema import StoryDraftRead, StoryPageRead


class EditorialProjectCreate(BaseModel):
    title: str
    slug: str
    description: str | None = None
    age_band: str
    content_lane_key: str | None = None
    language: str = "en"
    status: str = "draft"
    assigned_editor_user_id: int | None = None
    source_type: str = "manual"
    notes: str | None = None


class EditorialProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: str | None = None
    age_band: str
    content_lane_key: str | None = None
    language: str
    status: str
    created_by_user_id: int | None = None
    assigned_editor_user_id: int | None = None
    source_type: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class EditorialProjectUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    language: str | None = None
    status: str | None = None
    assigned_editor_user_id: int | None = None
    source_type: str | None = None
    notes: str | None = None


class EditorialAssetCreate(BaseModel):
    project_id: int
    asset_type: str
    file_url: str
    language: str | None = None
    page_number: int | None = None
    is_active: bool = True


class EditorialAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    asset_type: str
    file_url: str
    language: str | None = None
    page_number: int | None = None
    is_active: bool
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class EditorialAssetUpdate(BaseModel):
    asset_type: str | None = None
    file_url: str | None = None
    language: str | None = None
    page_number: int | None = None
    is_active: bool | None = None


class ManualStoryDraftCreate(BaseModel):
    title: str
    full_text: str
    summary: str
    age_band: str
    content_lane_key: str | None = None
    language: str = "en"
    review_status: str = "draft_pending_review"
    project_id: int | None = None
    read_time_minutes: int | None = None


class ManualStoryDraftUpdate(BaseModel):
    title: str | None = None
    full_text: str | None = None
    summary: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    language: str | None = None
    review_status: str | None = None
    project_id: int | None = None
    read_time_minutes: int | None = None
    review_notes: str | None = None
    approved_text: str | None = None


class ManualStoryPageCreate(BaseModel):
    story_draft_id: int
    page_number: int
    page_text: str
    scene_summary: str
    location: str
    mood: str
    characters_present: str
    illustration_prompt: str | None = None
    image_url: str | None = None


class ManualStoryPageUpdate(BaseModel):
    page_number: int | None = None
    page_text: str | None = None
    scene_summary: str | None = None
    location: str | None = None
    mood: str | None = None
    characters_present: str | None = None
    illustration_prompt: str | None = None
    image_url: str | None = None


class PreviewBookResponse(BaseModel):
    book: BookRead
    pages: list[BookPageRead]
    preview_only: bool


class EditorialProjectDraftResponse(BaseModel):
    draft: StoryDraftRead | None
    pages: list[StoryPageRead]
    preview_book: BookRead | None


class EditorialQualityRunResponse(BaseModel):
    draft_checks: list[QualityCheckRead]
    page_checks: list[QualityCheckRead]
