from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class EarnedAchievement(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "achievement_definition_id",
            "user_id",
            "child_profile_id",
            name="uq_earned_achievement_definition_user_child",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    achievement_definition_id: int = Field(foreign_key="achievementdefinition.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    earned_at: datetime = Field(default_factory=utc_now, nullable=False)
    source_table: str | None = None
    source_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
