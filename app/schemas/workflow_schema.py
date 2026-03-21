from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkflowJobCreate(BaseModel):
    job_type: str
    priority: int = 5
    payload_json: str
    scheduled_for: datetime | None = None
    max_attempts: int = 1
    parent_job_id: int | None = None


class WorkflowJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    status: str
    priority: int
    payload_json: str
    result_json: str | None = None
    error_message: str | None = None
    created_by_user_id: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    scheduled_for: datetime | None = None
    attempt_count: int
    max_attempts: int
    parent_job_id: int | None = None
    created_at: datetime
    updated_at: datetime


class WorkflowJobUpdate(BaseModel):
    status: str | None = None
    result_json: str | None = None
    error_message: str | None = None
    attempt_count: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class GenerateIdeasJobRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)
    age_band: str = "3-7"
    content_lane_key: str | None = None
    tone: str = "calm, gentle, plot-led"
    include_characters: list[str] | None = None
    bedtime_only: bool = True


class GenerateDraftJobRequest(BaseModel):
    story_idea_id: int


class GenerateIllustrationPlanJobRequest(BaseModel):
    story_draft_id: int
    min_pages: int = Field(default=8, ge=1)
    max_pages: int = Field(default=14, ge=1)


class GeneratePageIllustrationsJobRequest(BaseModel):
    story_draft_id: int
    page_ids: list[int] | None = None


class AssembleBookJobRequest(BaseModel):
    story_draft_id: int
    language: str = "en"
    content_lane_key: str | None = None
    publish_immediately: bool = False
    replace_existing: bool = True


class FullStoryPipelineJobRequest(BaseModel):
    story_idea_id: int | None = None
    auto_generate_idea_if_missing: bool = False
    publish_immediately: bool = False
    generate_mock_illustrations: bool = True
    auto_approve_illustrations: bool = False


class GenerateNarrationJobRequest(BaseModel):
    book_id: int
    voice_key: str
    language: str = "en"
    replace_existing: bool = False


class GenerateDailyStorySuggestionJobRequest(BaseModel):
    user_id: int
    child_profile_id: int | None = None
    date: str | None = None


class WorkflowJobRunResponse(BaseModel):
    job: WorkflowJobRead


class WorkflowQueueResponse(BaseModel):
    items: list[WorkflowJobRead]
