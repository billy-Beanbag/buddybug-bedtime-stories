from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class IllustrationCreate(SQLModel):
    story_page_id: int
    prompt_used: str
    image_url: str
    version_number: int = 1
    approval_status: str = "generated"
    provider: str = "manual_upload"
    provider_image_id: str | None = None
    generation_notes: str | None = None


class IllustrationRead(IllustrationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class IllustrationUpdate(SQLModel):
    story_page_id: int | None = None
    prompt_used: str | None = None
    image_url: str | None = None
    version_number: int | None = None
    approval_status: str | None = None
    provider: str | None = None
    provider_image_id: str | None = None
    generation_notes: str | None = None


class IllustrationGenerateRequest(SQLModel):
    story_page_id: int
    provider: str | None = None
    override_prompt: str | None = None
    generation_notes: str | None = None


class IllustrationGenerateResponse(SQLModel):
    illustration: IllustrationRead
    story_page_id: int
    image_status: str


class IllustrationApprovalRequest(SQLModel):
    generation_notes: str | None = None


class IllustrationPromptPreviewRequest(SQLModel):
    story_page_id: int
    provider: str | None = None
    override_prompt: str | None = None


class IllustrationPromptPackageRead(SQLModel):
    story_page_id: int
    provider: str
    provider_model: str | None = None
    provider_base_url: str | None = None
    provider_timeout_seconds: int | None = None
    generation_ready: bool
    live_generation_available: bool
    debug_enabled: bool = False
    prompt_used: str
    positive_prompt: str
    negative_prompt: str = ""
    page_text: str
    scene_summary: str
    location: str
    mood: str
    characters_present: str
    reference_assets: list["IllustrationReferenceAssetRead"] = Field(default_factory=list)
    reference_summary: str = ""


class IllustrationReferenceAssetRead(SQLModel):
    id: int
    name: str
    reference_type: str
    target_type: str | None = None
    target_id: int | None = None
    image_url: str
    prompt_notes: str | None = None
    language: str | None = None
    is_active: bool
