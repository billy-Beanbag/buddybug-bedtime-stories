from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class IllustrationQualityReview(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    illustration_id: int = Field(foreign_key="illustration.id", index=True)
    story_id: int | None = Field(default=None, foreign_key="storydraft.id", index=True)
    style_consistency_score: int
    character_consistency_score: int
    color_palette_score: int
    flagged_issues_json: str
    review_required: bool = Field(default=False, index=True)
    evaluated_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
