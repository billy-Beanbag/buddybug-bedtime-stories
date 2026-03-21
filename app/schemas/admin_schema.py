from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PipelineCountsResponse(BaseModel):
    idea_pending: int
    idea_selected: int
    draft_pending_review: int
    needs_revision: int
    approved_for_illustration: int
    story_pages_prompt_ready: int
    story_pages_image_generated: int
    story_pages_image_approved: int
    story_pages_image_rejected: int
    illustrations_generated: int
    illustrations_approved: int
    illustrations_rejected: int
    books_ready: int
    books_published: int
    audio_generated: int
    audio_approved: int
    audio_rejected: int
    workflow_jobs_queued: int
    workflow_jobs_running: int
    workflow_jobs_failed: int
    automation_schedules_active: int
    automation_schedules_due: int


class AdminStoryIdeaSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    premise: str
    age_band: str
    content_lane_key: str | None = None
    tone: str
    setting: str
    theme: str
    status: str
    created_at: datetime


class AdminStoryDraftSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_idea_id: int | None = None
    title: str
    age_band: str
    language: str
    content_lane_key: str | None = None
    summary: str
    review_status: str
    read_time_minutes: int
    created_at: datetime
    updated_at: datetime


class AdminStoryPageSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_draft_id: int
    page_number: int
    scene_summary: str
    image_status: str
    created_at: datetime
    updated_at: datetime


class AdminIllustrationSummary(BaseModel):
    id: int
    story_page_id: int
    story_draft_id: int | None = None
    story_draft_title: str | None = None
    book_id: int | None = None
    page_number: int | None = None
    scene_summary: str | None = None
    approval_status: str
    provider: str
    version_number: int
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminBookSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_draft_id: int
    title: str
    age_band: str
    language: str
    content_lane_key: str | None = None
    publication_status: str
    published: bool
    audio_available: bool
    created_at: datetime
    updated_at: datetime


class AdminAudioSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    voice_id: int
    approval_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminNextActionItem(BaseModel):
    stage: str
    entity_type: str
    entity_id: int
    title: str
    status: str
    suggested_action: str
    created_at: datetime


class AdminNextActionsResponse(BaseModel):
    items: list[AdminNextActionItem]
