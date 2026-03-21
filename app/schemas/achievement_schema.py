from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AchievementDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    description: str
    icon_key: str | None = None
    target_scope: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EarnedAchievementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    achievement_definition_id: int
    user_id: int
    child_profile_id: int | None = None
    earned_at: datetime
    source_table: str | None = None
    source_id: str | None = None
    created_at: datetime
    updated_at: datetime
    achievement_key: str | None = None
    title: str | None = None
    description: str | None = None
    icon_key: str | None = None
    target_scope: str | None = None


class ReadingStreakSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    child_profile_id: int | None = None
    current_streak_days: int
    longest_streak_days: int
    last_read_date: date | None = None
    created_at: datetime
    updated_at: datetime


class AchievementDashboardResponse(BaseModel):
    earned_achievements: list[EarnedAchievementRead]
    current_streak: int
    longest_streak: int
    next_suggested_milestone: str | None = None
