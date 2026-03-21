from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import StoryDraft, StoryIdea
from app.schemas.story_schema import (
    StoryDraftCreate,
    StoryDraftGenerateRequest,
    StoryDraftRead,
    StoryDraftUpdate,
)
from app.services.review_service import (
    approve_story_draft as approve_story_draft_review,
    get_story_draft_or_404,
    persist_story_draft,
    set_review_status,
    utc_now,
    validate_review_status,
)
from app.services.story_brief_service import upsert_story_brief_record
from app.services.story_review_queue_service import upsert_story_review_queue_item
from app.services.story_writer import generate_story_draft_payload
from app.services.i18n_service import validate_language_code
from app.services.story_quality_service import evaluate_story_quality
from app.utils.dependencies import get_current_editor_user

router = APIRouter(
    prefix="/story-drafts",
    tags=["story-drafts"],
    dependencies=[Depends(get_current_editor_user)],
)


def _get_story_idea_or_404(session: Session, story_idea_id: int) -> StoryIdea:
    story_idea = session.get(StoryIdea, story_idea_id)
    if story_idea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story idea not found")
    return story_idea


def _queue_status_for_review_status(review_status: str) -> str:
    return {
        "draft_pending_review": "pending_review",
        "review_pending": "pending_review",
        "needs_revision": "needs_edit",
        "approved_for_illustration": "approved",
        "rejected": "rejected",
    }.get(review_status, "pending_review")


@router.post(
    "/generate",
    response_model=StoryDraftRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a full story draft from a story idea",
)
def generate_story_draft(
    payload: StoryDraftGenerateRequest,
    session: Session = Depends(get_session),
) -> StoryDraft:
    story_idea = _get_story_idea_or_404(session, payload.story_idea_id)
    generated = generate_story_draft_payload(story_idea, session=session)

    story_draft = StoryDraft(
        story_idea_id=story_idea.id,
        title=generated.title,
        age_band=story_idea.age_band,
        language="en",
        content_lane_key=generated.content_lane_key,
        full_text=generated.full_text,
        summary=generated.summary,
        read_time_minutes=generated.read_time_minutes,
        review_status=generated.review_status,
        generation_source=generated.generation_source,
    )
    session.add(story_draft)

    story_idea.status = "converted_to_draft"
    story_idea.updated_at = utc_now()
    session.add(story_idea)

    session.commit()
    session.refresh(story_draft)
    upsert_story_brief_record(
        session,
        story_idea_id=story_idea.id,
        story_brief=generated.story_brief,
    )
    upsert_story_review_queue_item(
        session,
        story_id=story_draft.id,
        generated_story=generated.generated_story,
        rewritten_story=generated.rewritten_story,
        story_brief=generated.story_brief,
        story_validation=generated.story_validation,
        outline=generated.story_outline,
        illustration_scenes=generated.illustration_scenes,
        story_metadata=generated.story_metadata,
        status=_queue_status_for_review_status(generated.review_status),
    )
    evaluate_story_quality(session, story_id=story_draft.id)
    return story_draft


@router.post(
    "/delete-workflow-record",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a workflow record (book, draft, idea) and all dependencies",
)
def delete_workflow_record_route(
    book_id: int | None = Query(default=None),
    draft_id: int | None = Query(default=None),
    idea_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
) -> Response:
    if not any([book_id is not None, draft_id is not None, idea_id is not None]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of book_id, draft_id, or idea_id is required",
        )
    delete_workflow_record(session, book_id=book_id, draft_id=draft_id, idea_id=idea_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("", response_model=list[StoryDraftRead], summary="List story drafts")
def list_story_drafts(
    review_status: str | None = Query(default=None),
    story_idea_id: int | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[StoryDraft]:
    statement = select(StoryDraft).order_by(StoryDraft.created_at.desc()).limit(limit)
    if review_status:
        statement = statement.where(StoryDraft.review_status == review_status)
    if story_idea_id is not None:
        statement = statement.where(StoryDraft.story_idea_id == story_idea_id)
    if content_lane_key is not None:
        statement = statement.where(StoryDraft.content_lane_key == content_lane_key)
    return list(session.exec(statement).all())


@router.post(
    "",
    response_model=StoryDraftRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a story draft manually",
)
def create_story_draft(
    payload: StoryDraftCreate,
    session: Session = Depends(get_session),
) -> StoryDraft:
    story_idea = _get_story_idea_or_404(session, payload.story_idea_id) if payload.story_idea_id is not None else None
    story_draft = StoryDraft.model_validate(
        payload.model_copy(
            update={
                "age_band": story_idea.age_band if story_idea is not None else payload.age_band,
                "content_lane_key": payload.content_lane_key or (story_idea.content_lane_key if story_idea is not None else None),
                "language": validate_language_code(payload.language),
            }
        )
    )
    validate_review_status(story_draft.review_status)
    return persist_story_draft(session, story_draft)


@router.get("/{draft_id}", response_model=StoryDraftRead, summary="Get a story draft by id")
def get_story_draft(draft_id: int, session: Session = Depends(get_session)) -> StoryDraft:
    return get_story_draft_or_404(session, draft_id)


@router.patch(
    "/{draft_id}",
    response_model=StoryDraftRead,
    summary="Partially update a story draft",
)
def update_story_draft(
    draft_id: int,
    payload: StoryDraftUpdate,
    session: Session = Depends(get_session),
) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "story_idea_id" in update_data and update_data["story_idea_id"] is not None:
        story_idea = _get_story_idea_or_404(session, update_data["story_idea_id"])
        if "content_lane_key" not in update_data:
            update_data["content_lane_key"] = story_idea.content_lane_key
        if "age_band" not in update_data:
            update_data["age_band"] = story_idea.age_band
    if "review_status" in update_data and update_data["review_status"] is not None:
        validate_review_status(update_data["review_status"])
    if "language" in update_data and update_data["language"] is not None:
        update_data["language"] = validate_language_code(update_data["language"])

    for field_name, value in update_data.items():
        setattr(story_draft, field_name, value)

    story_draft.updated_at = utc_now()
    return persist_story_draft(session, story_draft)


@router.delete(
    "/{draft_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a story draft",
)
def delete_story_draft(draft_id: int, session: Session = Depends(get_session)) -> Response:
    story_draft = get_story_draft_or_404(session, draft_id)
    session.delete(story_draft)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{draft_id}/submit-for-review",
    response_model=StoryDraftRead,
    summary="Submit a story draft for review",
)
def submit_for_review(draft_id: int, session: Session = Depends(get_session)) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    return set_review_status(session, story_draft, "draft_pending_review")


@router.post(
    "/{draft_id}/mark-needs-revision",
    response_model=StoryDraftRead,
    summary="Mark a story draft as needing revision",
)
def mark_needs_revision(draft_id: int, session: Session = Depends(get_session)) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    return set_review_status(session, story_draft, "needs_revision")


@router.post(
    "/{draft_id}/approve",
    response_model=StoryDraftRead,
    summary="Approve a story draft for illustration",
)
def approve_story_draft(draft_id: int, session: Session = Depends(get_session)) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    return approve_story_draft_review(session, story_draft)


@router.post(
    "/{draft_id}/reject",
    response_model=StoryDraftRead,
    summary="Reject a story draft",
)
def reject_story_draft(draft_id: int, session: Session = Depends(get_session)) -> StoryDraft:
    story_draft = get_story_draft_or_404(session, draft_id)
    return set_review_status(session, story_draft, "rejected")
