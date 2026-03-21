from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session, select

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import StoryDraft, User
from app.schemas.story_review_queue_schema import StoryReviewQueueRead
from app.schemas.story_schema import (
    StoryDraftReviewActionRequest,
    StoryDraftReviewRead,
    StoryDraftReviewUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.review_service import (
    QUEUE_REVIEW_STATUSES,
    approve_story_draft,
    apply_review_update,
    get_story_draft_or_404,
    set_review_status,
    validate_review_status,
)
from app.services.story_review_queue_service import get_story_review_queue_item, list_story_review_queue_items
from app.utils.dependencies import get_current_editor_user

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
    dependencies=[Depends(get_current_editor_user)],
)


@router.get("/queue", response_model=list[StoryDraftReviewRead], summary="List drafts needing review")
def list_review_queue(
    review_status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[StoryDraft]:
    if review_status is not None:
        validate_review_status(review_status)
        statuses = [review_status]
    else:
        statuses = sorted(QUEUE_REVIEW_STATUSES)

    statement = (
        select(StoryDraft)
        .where(StoryDraft.review_status.in_(statuses))
        .order_by(StoryDraft.updated_at.desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


@router.get(
    "/story-queue",
    response_model=list[StoryReviewQueueRead],
    summary="List structured story packages awaiting human review",
)
def list_structured_story_queue(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    return list_story_review_queue_items(session, status=status, limit=limit)


@router.get(
    "/story-queue/{story_id}",
    response_model=StoryReviewQueueRead,
    summary="Get the structured review package for a story draft",
)
def get_structured_story_queue_item(story_id: int, session: Session = Depends(get_session)):
    queue_item = get_story_review_queue_item(session, story_id=story_id)
    if queue_item is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Structured review package not found")
    return queue_item


@router.get(
    "/drafts/{draft_id}",
    response_model=StoryDraftReviewRead,
    summary="Get review detail for a story draft",
)
def get_review_draft(draft_id: int, session: Session = Depends(get_session)) -> StoryDraft:
    return get_story_draft_or_404(session, draft_id)


@router.patch(
    "/drafts/{draft_id}",
    response_model=StoryDraftReviewRead,
    summary="Update review fields for a story draft",
)
def update_review_draft(
    draft_id: int,
    request: Request,
    payload: StoryDraftReviewUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    updated_draft = apply_review_update(
        session,
        story_draft,
        payload,
        created_by_user_id=current_user.id if current_user is not None else None,
    )
    create_audit_log(
        session,
        action_type="draft_review_updated",
        entity_type="story_draft",
        entity_id=str(updated_draft.id),
        summary=f"Updated review fields for draft '{updated_draft.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"review_status": updated_draft.review_status},
    )
    return updated_draft


@router.post(
    "/drafts/{draft_id}/approve",
    response_model=StoryDraftReviewRead,
    summary="Approve a story draft for illustration",
)
def approve_review_draft(
    draft_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    approved_draft = approve_story_draft(
        session,
        story_draft,
        created_by_user_id=current_user.id if current_user is not None else None,
    )
    create_audit_log(
        session,
        action_type="draft_approved",
        entity_type="story_draft",
        entity_id=str(approved_draft.id),
        summary=f"Approved draft '{approved_draft.title}' for illustration",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"review_status": approved_draft.review_status},
    )
    return approved_draft


@router.post(
    "/drafts/{draft_id}/needs-revision",
    response_model=StoryDraftReviewRead,
    summary="Mark a story draft as needing revision",
)
def mark_review_needs_revision(
    draft_id: int,
    request: Request,
    payload: StoryDraftReviewActionRequest | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    review_notes = payload.review_notes if payload is not None else None
    updated_draft = set_review_status(
        session,
        story_draft,
        "needs_revision",
        review_notes=review_notes,
        created_by_user_id=current_user.id if current_user is not None else None,
    )
    create_audit_log(
        session,
        action_type="draft_needs_revision",
        entity_type="story_draft",
        entity_id=str(updated_draft.id),
        summary=f"Marked draft '{updated_draft.title}' as needing revision",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"review_notes": review_notes},
    )
    return updated_draft


@router.post(
    "/drafts/{draft_id}/reject",
    response_model=StoryDraftReviewRead,
    summary="Reject a story draft",
)
def reject_review_draft(
    draft_id: int,
    request: Request,
    payload: StoryDraftReviewActionRequest | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    review_notes = payload.review_notes if payload is not None else None
    updated_draft = set_review_status(
        session,
        story_draft,
        "rejected",
        review_notes=review_notes,
        created_by_user_id=current_user.id if current_user is not None else None,
    )
    create_audit_log(
        session,
        action_type="draft_rejected",
        entity_type="story_draft",
        entity_id=str(updated_draft.id),
        summary=f"Rejected draft '{updated_draft.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"review_notes": review_notes},
    )
    return updated_draft


@router.post(
    "/drafts/{draft_id}/reset-to-review",
    response_model=StoryDraftReviewRead,
    summary="Reset a story draft back to pending review",
)
def reset_review_draft(
    draft_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    return set_review_status(
        session,
        story_draft,
        "draft_pending_review",
        created_by_user_id=current_user.id,
    )
