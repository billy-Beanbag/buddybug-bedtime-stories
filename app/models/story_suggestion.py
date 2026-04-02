from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StorySuggestion(SQLModel, table=True):
    """Parent-authored story brief that can influence future editorial direction."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    promoted_story_idea_id: int | None = Field(default=None, foreign_key="storyidea.id", index=True)
    title: str | None = None
    brief: str
    desired_outcome: str | None = None
    inspiration_notes: str | None = None
    avoid_notes: str | None = None
    age_band: str = Field(default="3-7", index=True)
    language: str = Field(default="en", index=True)
    status: str = Field(default="submitted", index=True)
    allow_reference_use: bool = Field(default=False)
    approved_as_reference: bool = Field(default=False, index=True)
    editorial_notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
