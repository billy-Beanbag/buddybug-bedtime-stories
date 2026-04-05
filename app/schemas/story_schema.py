from datetime import datetime

from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class StoryIdeaBase(SQLModel):
    title: str
    premise: str
    hook_type: str | None = None
    age_band: str
    content_lane_key: str | None = "bedtime_3_7"
    tone: str
    setting: str
    theme: str
    bedtime_feeling: str
    main_characters: str
    supporting_characters: str | None = None
    series_key: str | None = None
    series_title: str | None = None
    estimated_minutes: int
    status: str = "idea_pending"
    generation_source: str = "manual"


class StoryIdeaCreate(StoryIdeaBase):
    pass


class StoryIdeaRead(StoryIdeaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class StoryIdeaUpdate(SQLModel):
    title: str | None = None
    premise: str | None = None
    hook_type: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    tone: str | None = None
    setting: str | None = None
    theme: str | None = None
    bedtime_feeling: str | None = None
    main_characters: str | None = None
    supporting_characters: str | None = None
    series_key: str | None = None
    series_title: str | None = None
    estimated_minutes: int | None = None
    status: str | None = None
    generation_source: str | None = None


class StoryIdeaGenerateRequest(SQLModel):
    count: int = Field(default=5, ge=1, le=20)
    age_band: str = "3-7"
    content_lane_key: str | None = None
    tone: str = "calm, gentle, plot-led"
    include_characters: list[str] | None = None
    bedtime_only: bool = True


class IdeaGenerationSummary(SQLModel):
    """How the batch was produced (admin / debugging; no secrets)."""

    path: str = Field(
        description="llm | llm_plus_curated | curated",
    )
    excluded_recent_premise_count: int = Field(
        ge=0,
        description="Size of premise exclusion set (recent DB premises + merged LLM rows when applicable).",
    )
    approved_story_suggestion_count: int = Field(
        default=0,
        ge=0,
        description="How many approved reusable parent suggestions were fed into the prompt as editorial guidance.",
    )
    llm_idea_count: int = Field(ge=0)
    curated_idea_count: int = Field(ge=0)


class StoryIdeaBatchGenerateResponse(SQLModel):
    created_count: int
    ideas: list[StoryIdeaRead]
    generation_summary: IdeaGenerationSummary | None = None


class StoryIdeaSelectRequest(SQLModel):
    """Optional body for select endpoint: assign route (content_lane) when selecting."""

    content_lane_key: str | None = Field(
        default=None,
        description="Bedtime (bedtime_3_7) or Adventure (story_adventures_3_7). Assigns labels and age band.",
    )


class StoryDraftCreate(SQLModel):
    story_idea_id: int | None = None
    project_id: int | None = None
    classic_source_id: int | None = None
    title: str
    age_band: str = "3-7"
    language: str = "en"
    content_lane_key: str | None = "bedtime_3_7"
    is_classic: bool = False
    full_text: str
    summary: str
    read_time_minutes: int
    review_status: str = "draft_pending_review"
    review_notes: str | None = None
    approved_text: str | None = None
    generation_source: str = "manual"


class StoryDraftRead(StoryDraftCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class StoryDraftUpdate(SQLModel):
    story_idea_id: int | None = None
    project_id: int | None = None
    classic_source_id: int | None = None
    title: str | None = None
    age_band: str | None = None
    language: str | None = None
    content_lane_key: str | None = None
    is_classic: bool | None = None
    full_text: str | None = None
    summary: str | None = None
    read_time_minutes: int | None = None
    review_status: str | None = None
    review_notes: str | None = None
    approved_text: str | None = None
    generation_source: str | None = None


class StoryDraftGenerateRequest(SQLModel):
    story_idea_id: int


class StoryDraftReviewUpdate(SQLModel):
    title: str | None = None
    review_notes: str | None = None
    full_text: str | None = None
    approved_text: str | None = None
    review_status: str | None = None
    content_lane_key: str | None = None


class StoryDraftReviewRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_idea_id: int | None = None
    project_id: int | None = None
    title: str
    age_band: str
    language: str
    content_lane_key: str | None = None
    summary: str
    full_text: str
    approved_text: str | None = None
    review_status: str
    review_notes: str | None = None
    read_time_minutes: int
    generation_source: str
    created_at: datetime
    updated_at: datetime


class StoryDraftReviewActionRequest(SQLModel):
    review_notes: str | None = None


class StoryPageCreate(SQLModel):
    story_draft_id: int
    page_number: int
    page_text: str
    scene_summary: str
    location: str
    mood: str
    characters_present: str
    illustration_prompt: str
    image_status: str = "prompt_ready"
    image_url: str | None = None


class StoryPageRead(StoryPageCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class StoryPageUpdate(SQLModel):
    story_draft_id: int | None = None
    page_number: int | None = None
    page_text: str | None = None
    scene_summary: str | None = None
    location: str | None = None
    mood: str | None = None
    characters_present: str | None = None
    illustration_prompt: str | None = None
    image_status: str | None = None
    image_url: str | None = None


class IllustrationPlanGenerateRequest(SQLModel):
    story_draft_id: int
    target_page_count: int | None = None
    min_pages: int = Field(default=5, ge=1)
    max_pages: int = Field(default=6, ge=1)


class IllustrationPlanBatchResponse(SQLModel):
    story_draft_id: int
    created_count: int
    pages: list[StoryPageRead]
