from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class StoryQualityReview(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    story_id: int = Field(foreign_key="storydraft.id", index=True)
    quality_score: int
    review_required: bool = Field(default=False, index=True)
    flagged_issues_json: str
    evaluation_summary: str | None = None
    evaluated_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
