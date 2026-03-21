from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.config import STORY_GENERATION_DEBUG
from app.models import StoryReviewQueue
from app.schemas.story_pipeline_schema import (
    IllustrationScene,
    StoryBrief,
    StoryMetadata,
    StoryOutline,
    StoryValidationResult,
)

ALLOWED_QUEUE_STATUSES = {"pending_review", "approved", "rejected", "needs_edit"}
logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_story_review_queue_item(session: Session, *, story_id: int) -> StoryReviewQueue | None:
    statement = select(StoryReviewQueue).where(StoryReviewQueue.story_id == story_id)
    return session.exec(statement).first()


def list_story_review_queue_items(
    session: Session,
    *,
    status: str | None = None,
    limit: int = 50,
) -> list[StoryReviewQueue]:
    statement = select(StoryReviewQueue).order_by(StoryReviewQueue.updated_at.desc()).limit(limit)
    if status is not None:
        statement = statement.where(StoryReviewQueue.status == status)
    return list(session.exec(statement).all())


def upsert_story_review_queue_item(
    session: Session,
    *,
    story_id: int,
    generated_story: str,
    rewritten_story: str,
    story_brief: StoryBrief | None,
    story_validation: StoryValidationResult | None,
    outline: StoryOutline,
    illustration_scenes: list[IllustrationScene],
    story_metadata: StoryMetadata,
    status: str = "pending_review",
) -> StoryReviewQueue:
    if status not in ALLOWED_QUEUE_STATUSES:
        raise ValueError(f"Unsupported story review queue status: {status}")
    row = get_story_review_queue_item(session, story_id=story_id)
    if row is None:
        row = StoryReviewQueue(
            story_id=story_id,
            generated_story=generated_story,
            rewritten_story=rewritten_story,
            story_brief=json.dumps(story_brief.model_dump(), sort_keys=True) if story_brief is not None else None,
            story_validation=json.dumps(story_validation.model_dump(), sort_keys=True) if story_validation is not None else None,
            outline=json.dumps(outline.model_dump(), sort_keys=True),
            illustration_plan=json.dumps([scene.model_dump() for scene in illustration_scenes], sort_keys=True),
            story_metadata=json.dumps(story_metadata.model_dump(), sort_keys=True),
            status=status,
        )
    else:
        row.generated_story = generated_story
        row.rewritten_story = rewritten_story
        row.story_brief = json.dumps(story_brief.model_dump(), sort_keys=True) if story_brief is not None else None
        row.story_validation = (
            json.dumps(story_validation.model_dump(), sort_keys=True) if story_validation is not None else None
        )
        row.outline = json.dumps(outline.model_dump(), sort_keys=True)
        row.illustration_plan = json.dumps([scene.model_dump() for scene in illustration_scenes], sort_keys=True)
        row.story_metadata = json.dumps(story_metadata.model_dump(), sort_keys=True)
        row.status = status
    session.add(row)
    session.commit()
    session.refresh(row)
    if STORY_GENERATION_DEBUG:
        logger.info(
            "Story review queue updated: story_id=%s status=%s has_brief=%s has_validation=%s",
            row.story_id,
            row.status,
            bool(row.story_brief),
            bool(row.story_validation),
        )
    return row


def set_story_review_queue_status(session: Session, *, story_id: int, status: str) -> StoryReviewQueue | None:
    if status not in ALLOWED_QUEUE_STATUSES:
        raise ValueError(f"Unsupported story review queue status: {status}")
    row = get_story_review_queue_item(session, story_id=story_id)
    if row is None:
        return None
    row.status = status
    row.updated_at = _utc_now()
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
