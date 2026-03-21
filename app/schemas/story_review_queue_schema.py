from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StoryReviewQueueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_id: int
    generated_story: str
    rewritten_story: str
    story_brief: str | None = None
    story_validation: str | None = None
    outline: str
    illustration_plan: str
    story_metadata: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
