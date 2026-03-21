from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class FamilyDigestChildSummary(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "family_digest_id",
            "child_profile_id",
            name="uq_family_digest_child_summary_digest_child",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    family_digest_id: int = Field(foreign_key="familydigest.id", index=True)
    child_profile_id: int = Field(foreign_key="childprofile.id", index=True)
    stories_opened: int = Field(default=0)
    stories_completed: int = Field(default=0)
    narration_uses: int = Field(default=0)
    achievements_earned: int = Field(default=0)
    current_streak_days: int = Field(default=0)
    summary_text: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
