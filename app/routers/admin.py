from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.admin_schema import (
    AdminAudioSummary,
    AdminBookSummary,
    AdminIllustrationSummary,
    AdminNextActionsResponse,
    AdminStoryDraftSummary,
    AdminStoryIdeaSummary,
    AdminStoryPageSummary,
    PipelineCountsResponse,
)
from app.services.admin_service import (
    delete_workflow_record,
    get_approved_drafts_ready_for_planning,
    get_audio_awaiting_approval,
    get_books_ready_or_unpublished,
    get_draft_review_queue,
    get_idea_queue,
    get_illustrations_awaiting_approval,
    get_next_action_items,
    get_pipeline_counts,
    get_story_pages_needing_images,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin_user)],
)


def _do_remove_workflow_record(
    session: Session,
    *,
    book_id: int | None = None,
    draft_id: int | None = None,
    idea_id: int | None = None,
) -> None:
    if not any([book_id is not None, draft_id is not None, idea_id is not None]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of book_id, draft_id, or idea_id is required",
        )
    delete_workflow_record(session, book_id=book_id, draft_id=draft_id, idea_id=idea_id)


@router.delete(
    "/workflow/record",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a workflow record (book, draft, idea) and all dependencies",
)
def remove_workflow_record_delete(
    book_id: int | None = Query(default=None),
    draft_id: int | None = Query(default=None),
    idea_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
):
    _do_remove_workflow_record(session, book_id=book_id, draft_id=draft_id, idea_id=idea_id)


@router.post(
    "/workflow/record/remove",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a workflow record (POST fallback for clients that block DELETE)",
)
def remove_workflow_record_post(
    book_id: int | None = Query(default=None),
    draft_id: int | None = Query(default=None),
    idea_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
):
    _do_remove_workflow_record(session, book_id=book_id, draft_id=draft_id, idea_id=idea_id)


@router.get("/pipeline-counts", response_model=PipelineCountsResponse, summary="Get workflow pipeline counts")
def pipeline_counts(session: Session = Depends(get_session)) -> PipelineCountsResponse:
    return get_pipeline_counts(session)


@router.get("/ideas/queue", response_model=list[AdminStoryIdeaSummary], summary="List story ideas in the admin queue")
def idea_queue(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=300),
    session: Session = Depends(get_session),
) -> list[AdminStoryIdeaSummary]:
    return get_idea_queue(session, status=status, limit=limit)


@router.get("/drafts/queue", response_model=list[AdminStoryDraftSummary], summary="List drafts in the review queue")
def draft_queue(
    review_status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=300),
    session: Session = Depends(get_session),
) -> list[AdminStoryDraftSummary]:
    return get_draft_review_queue(session, review_status=review_status, limit=limit)


@router.get(
    "/drafts/ready-for-planning",
    response_model=list[AdminStoryDraftSummary],
    summary="List approved drafts that do not yet have story pages",
)
def drafts_ready_for_planning(
    limit: int = Query(default=50, ge=1, le=300),
    session: Session = Depends(get_session),
) -> list[AdminStoryDraftSummary]:
    return get_approved_drafts_ready_for_planning(session, limit=limit)


@router.get(
    "/story-pages/queue",
    response_model=list[AdminStoryPageSummary],
    summary="List story pages waiting for image workflow actions",
)
def story_page_queue(
    image_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[AdminStoryPageSummary]:
    return get_story_pages_needing_images(session, image_status=image_status, limit=limit)


@router.get(
    "/illustrations/queue",
    response_model=list[AdminIllustrationSummary],
    summary="List illustrations in the moderation queue",
)
def illustration_queue(
    approval_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[AdminIllustrationSummary]:
    return get_illustrations_awaiting_approval(session, approval_status=approval_status, limit=limit)


@router.get("/books/queue", response_model=list[AdminBookSummary], summary="List books in the publishing queue")
def book_queue(
    publication_status: str | None = Query(default=None),
    published: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[AdminBookSummary]:
    return get_books_ready_or_unpublished(
        session,
        publication_status=publication_status,
        published=published,
        limit=limit,
    )


@router.get("/audio/queue", response_model=list[AdminAudioSummary], summary="List audio assets in the approval queue")
def audio_queue(
    approval_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[AdminAudioSummary]:
    return get_audio_awaiting_approval(session, approval_status=approval_status, limit=limit)


@router.get("/next-actions", response_model=AdminNextActionsResponse, summary="Get prioritized next workflow actions")
def next_actions(
    limit: int = Query(default=25, ge=1, le=200),
    session: Session = Depends(get_session),
) -> AdminNextActionsResponse:
    return AdminNextActionsResponse(items=get_next_action_items(session, limit=limit))
