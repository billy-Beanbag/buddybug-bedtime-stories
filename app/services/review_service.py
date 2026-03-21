from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import StoryDraft
from app.schemas.story_schema import StoryDraftReviewUpdate
from app.services.content_lane_service import validate_content_lane_key
from app.services.content_version_service import snapshot_story_draft
from app.services.story_review_queue_service import set_story_review_queue_status
from app.services.style_engine import queue_story_edit_training_record

ALLOWED_REVIEW_STATUSES = {
    "draft_generated",
    "draft_pending_review",
    "review_pending",
    "needs_revision",
    "approved_for_illustration",
    "rejected",
}

QUEUE_REVIEW_STATUSES = {"draft_pending_review", "review_pending", "needs_revision"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_story_draft_or_404(session: Session, draft_id: int) -> StoryDraft:
    story_draft = session.get(StoryDraft, draft_id)
    if story_draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")
    return story_draft


def validate_review_status(review_status: str) -> str:
    if review_status not in ALLOWED_REVIEW_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review status")
    return review_status


def persist_story_draft(session: Session, story_draft: StoryDraft) -> StoryDraft:
    session.add(story_draft)
    session.commit()
    session.refresh(story_draft)
    return story_draft


def apply_review_update(
    session: Session,
    story_draft: StoryDraft,
    payload: StoryDraftReviewUpdate,
    *,
    created_by_user_id: int | None = None,
) -> StoryDraft:
    update_data = payload.model_dump(exclude_unset=True)
    original_text = story_draft.approved_text or story_draft.full_text or ""

    if "review_status" in update_data and update_data["review_status"] is not None:
        validate_review_status(update_data["review_status"])

    if "content_lane_key" in update_data and update_data["content_lane_key"] is not None:
        lane = validate_content_lane_key(
            session,
            age_band=None,
            content_lane_key=update_data["content_lane_key"],
        )
        update_data["content_lane_key"] = lane.key

    changed = False
    for field_name, value in update_data.items():
        if getattr(story_draft, field_name) != value:
            changed = True
    if changed:
        snapshot_story_draft(session, story_draft=story_draft, created_by_user_id=created_by_user_id)
    candidate_text = (
        update_data.get("approved_text")
        if isinstance(update_data.get("approved_text"), str)
        else update_data.get("full_text")
    )
    if isinstance(candidate_text, str) and candidate_text.strip() and candidate_text.strip() != original_text.strip():
        queue_story_edit_training_record(
            session,
            original_story=original_text,
            edited_story=candidate_text,
            edit_notes=update_data.get("review_notes"),
        )
    for field_name, value in update_data.items():
        setattr(story_draft, field_name, value)

    if changed:
        story_draft.updated_at = utc_now()
    if "review_status" in update_data and update_data["review_status"] is not None:
        queue_status = {
            "draft_pending_review": "pending_review",
            "review_pending": "pending_review",
            "needs_revision": "needs_edit",
            "rejected": "rejected",
            "approved_for_illustration": "approved",
        }.get(update_data["review_status"])
        if queue_status is not None:
            set_story_review_queue_status(session, story_id=story_draft.id, status=queue_status)

    return persist_story_draft(session, story_draft)


def set_review_status(
    session: Session,
    story_draft: StoryDraft,
    review_status: str,
    review_notes: str | None = None,
    *,
    created_by_user_id: int | None = None,
) -> StoryDraft:
    validate_review_status(review_status)
    changed = review_status != story_draft.review_status or (review_notes is not None and review_notes != story_draft.review_notes)
    if changed:
        snapshot_story_draft(session, story_draft=story_draft, created_by_user_id=created_by_user_id)
    story_draft.review_status = review_status
    if review_notes is not None:
        story_draft.review_notes = review_notes
    story_draft.updated_at = utc_now()
    queue_status = {
        "draft_pending_review": "pending_review",
        "review_pending": "pending_review",
        "needs_revision": "needs_edit",
        "rejected": "rejected",
        "approved_for_illustration": "approved",
    }.get(review_status)
    if queue_status is not None:
        set_story_review_queue_status(session, story_id=story_draft.id, status=queue_status)
    return persist_story_draft(session, story_draft)


def approve_story_draft(session: Session, story_draft: StoryDraft, *, created_by_user_id: int | None = None) -> StoryDraft:
    changed = story_draft.review_status != "approved_for_illustration" or not story_draft.approved_text
    if changed:
        snapshot_story_draft(session, story_draft=story_draft, created_by_user_id=created_by_user_id)
    story_draft.review_status = "approved_for_illustration"
    if not story_draft.approved_text:
        story_draft.approved_text = story_draft.full_text
    story_draft.updated_at = utc_now()
    set_story_review_queue_status(session, story_id=story_draft.id, status="approved")
    return persist_story_draft(session, story_draft)
