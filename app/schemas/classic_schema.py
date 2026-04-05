from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.book_schema import BookPageRead, BookRead
from app.schemas.story_schema import StoryDraftRead, StoryPageRead


class ClassicSourceCreate(BaseModel):
    title: str = Field(min_length=1)
    source_text: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    public_domain_verified: bool = False
    source_author: str | None = None
    source_origin_notes: str | None = None


class ClassicSourceUpdate(BaseModel):
    title: str | None = None
    source_text: str | None = None
    source_url: str | None = None
    public_domain_verified: bool | None = None
    source_author: str | None = None
    source_origin_notes: str | None = None
    import_status: str | None = None


class ClassicSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_text: str
    source_url: str
    public_domain_verified: bool
    source_author: str | None = None
    source_origin_notes: str | None = None
    import_status: str
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ClassicAdaptationCreateRequest(BaseModel):
    age_band: str = "3-7"
    content_lane_key: str | None = "bedtime_3_7"
    language: str = "en"
    adaptation_intensity: str = "light"
    min_pages: int = Field(default=5, ge=1, le=20)
    max_pages: int = Field(default=6, ge=1, le=24)


class ClassicAdaptationUpdate(BaseModel):
    adapted_title: str | None = None
    adapted_text: str | None = None
    adaptation_intensity: str | None = None
    adaptation_notes: str | None = None
    cameo_insertions_summary: str | None = None
    scene_seed_notes_json: str | None = None
    validation_status: str | None = None
    validation_warnings_json: str | None = None
    review_status: str | None = None
    illustration_status: str | None = None
    editor_notes: str | None = None


class ClassicApproveRequest(BaseModel):
    editor_notes: str | None = None


class ClassicAdaptationDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    classic_source_id: int
    project_id: int | None = None
    story_draft_id: int | None = None
    preview_book_id: int | None = None
    adapted_title: str
    adapted_text: str
    adaptation_intensity: str
    adaptation_notes: str | None = None
    cameo_insertions_summary: str | None = None
    scene_seed_notes_json: str | None = None
    page_scene_data_json: str | None = None
    validation_status: str
    validation_warnings_json: str | None = None
    illustration_status: str
    review_status: str
    editor_notes: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ClassicDraftBundleResponse(BaseModel):
    source: ClassicSourceRead
    adaptation: ClassicAdaptationDraftRead
    story_draft: StoryDraftRead | None = None
    story_pages: list[StoryPageRead]
    preview_book: BookRead | None = None
    preview_pages: list[BookPageRead]


class ClassicIllustrationGenerationResponse(BaseModel):
    classic_adaptation_draft_id: int
    story_draft_id: int
    generated_count: int
    illustration_ids: list[int]
    page_ids: list[int]
    provider: str


class ClassicPublishResponse(BaseModel):
    source: ClassicSourceRead
    adaptation: ClassicAdaptationDraftRead
    book: BookRead
