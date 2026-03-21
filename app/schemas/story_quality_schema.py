from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StoryQualityReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_id: int
    quality_score: int
    review_required: bool
    flagged_issues_json: str
    evaluation_summary: str | None = None
    evaluated_at: datetime
    created_at: datetime
    updated_at: datetime


class IllustrationQualityReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    illustration_id: int
    story_id: int | None = None
    style_consistency_score: int
    character_consistency_score: int
    color_palette_score: int
    flagged_issues_json: str
    review_required: bool
    evaluated_at: datetime
    created_at: datetime
    updated_at: datetime


class StoryQualitySummaryResponse(BaseModel):
    story_id: int
    quality_score: int
    review_required: bool
    flagged_issues: list[str]


class StoryQualityQueueItemResponse(BaseModel):
    story_id: int
    title: str
    review_status: str
    quality_score: int
    review_required: bool
    flagged_issues: list[str]
    evaluation_summary: str | None = None
    evaluated_at: datetime


class StoryQualityDetailResponse(BaseModel):
    story_quality_review: StoryQualityReviewRead
    illustration_reviews: list[IllustrationQualityReviewRead]
    summary: StoryQualitySummaryResponse
