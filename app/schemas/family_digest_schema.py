from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class FamilyDigestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    digest_type: str
    period_start: date
    period_end: date
    title: str
    summary_json: str
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


class FamilyDigestChildSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_digest_id: int
    child_profile_id: int
    stories_opened: int
    stories_completed: int
    narration_uses: int
    achievements_earned: int
    current_streak_days: int
    summary_text: str | None = None
    created_at: datetime
    updated_at: datetime


class FamilyDigestDetailResponse(BaseModel):
    digest: FamilyDigestRead
    child_summaries: list[FamilyDigestChildSummaryRead]


class FamilyDigestGenerateResponse(BaseModel):
    digest: FamilyDigestRead
    child_summaries: list[FamilyDigestChildSummaryRead]
    generated_now: bool


class FamilyDigestSummaryCardResponse(BaseModel):
    title: str
    highlight_text: str
    period_start: date
    period_end: date
    child_count: int
    stories_completed: int
    achievements_earned: int
