from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.story_quality_schema import (
    IllustrationQualityReviewRead,
    StoryQualityDetailResponse,
    StoryQualityQueueItemResponse,
    StoryQualityReviewRead,
    StoryQualitySummaryResponse,
)
from app.services.story_quality_service import (
    build_story_quality_summary,
    get_latest_illustration_quality_reviews,
    get_or_create_story_quality_review,
    list_story_quality_review_queue,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(tags=["story-quality"])
admin_router = APIRouter(prefix="/admin/story-quality", tags=["admin-story-quality"])


@router.get("/stories/{story_id}/quality", response_model=StoryQualitySummaryResponse, summary="Get story quality summary")
def get_story_quality_summary(
    story_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_active_user),
) -> StoryQualitySummaryResponse:
    return StoryQualitySummaryResponse(**build_story_quality_summary(session, story_id=story_id))


@admin_router.get(
    "/review-queue",
    response_model=list[StoryQualityQueueItemResponse],
    summary="List stories flagged by automated quality review",
)
def get_story_quality_review_queue(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[StoryQualityQueueItemResponse]:
    return [StoryQualityQueueItemResponse(**item) for item in list_story_quality_review_queue(session)]


@admin_router.get("/{story_id}", response_model=StoryQualityDetailResponse, summary="Get full quality review detail for one story")
def get_story_quality_detail(
    story_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> StoryQualityDetailResponse:
    story_review = get_or_create_story_quality_review(session, story_id=story_id)
    illustration_reviews = get_latest_illustration_quality_reviews(session, story_id=story_id)
    summary = build_story_quality_summary(session, story_id=story_id)
    return StoryQualityDetailResponse(
        story_quality_review=StoryQualityReviewRead.model_validate(story_review),
        illustration_reviews=[IllustrationQualityReviewRead.model_validate(item) for item in illustration_reviews],
        summary=StoryQualitySummaryResponse(**summary),
    )
