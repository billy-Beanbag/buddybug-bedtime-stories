from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StoryDraftVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_draft_id: int
    version_number: int
    title: str
    full_text: str
    summary: str
    review_status: str
    review_notes: str | None = None
    approved_text: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime


class StoryPageVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_page_id: int
    version_number: int
    page_number: int
    page_text: str
    scene_summary: str
    location: str
    mood: str
    characters_present: str
    illustration_prompt: str
    image_url: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime


class RollbackResponse(BaseModel):
    ok: bool = True
    message: str
    entity_type: str
    entity_id: int
    rolled_back_to_version_id: int
