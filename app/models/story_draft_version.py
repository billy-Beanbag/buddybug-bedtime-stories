from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class StoryDraftVersion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    story_draft_id: int = Field(foreign_key="storydraft.id", index=True)
    version_number: int
    title: str
    full_text: str
    summary: str
    review_status: str
    review_notes: str | None = None
    approved_text: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
