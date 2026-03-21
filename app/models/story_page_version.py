from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class StoryPageVersion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    story_page_id: int = Field(foreign_key="storypage.id", index=True)
    version_number: int
    page_number: int
    page_text: str
    scene_summary: str
    location: str
    mood: str
    characters_present: str
    illustration_prompt: str
    image_url: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
