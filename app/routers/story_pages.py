from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Illustration, StoryDraft, StoryIdea, StoryPage
from app.schemas.story_schema import (
    IllustrationPlanBatchResponse,
    IllustrationPlanGenerateRequest,
    StoryPageCreate,
    StoryPageRead,
    StoryPageUpdate,
)
from app.services.illustration_planner import generate_story_page_payloads
from app.services.review_service import utc_now
from app.utils.dependencies import get_current_editor_user

IMAGE_STATUSES = {
    "not_started",
    "prompt_ready",
    "image_generated",
    "image_approved",
    "image_rejected",
}

router = APIRouter(
    prefix="/story-pages",
    tags=["story-pages"],
    dependencies=[Depends(get_current_editor_user)],
)


def _get_story_draft_or_404(session: Session, story_draft_id: int) -> StoryDraft:
    story_draft = session.get(StoryDraft, story_draft_id)
    if story_draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")
    return story_draft


def _get_story_page_or_404(session: Session, page_id: int) -> StoryPage:
    story_page = session.get(StoryPage, page_id)
    if story_page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story page not found")
    return story_page


def _validate_image_status(image_status: str) -> str:
    if image_status not in IMAGE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image status")
    return image_status


def _persist_story_page(session: Session, story_page: StoryPage) -> StoryPage:
    session.add(story_page)
    session.commit()
    session.refresh(story_page)
    return story_page


@router.get(
    "/by-draft/{story_draft_id}",
    response_model=list[StoryPageRead],
    summary="Get ordered page plans for one story draft",
)
def get_story_pages_by_draft(
    story_draft_id: int,
    session: Session = Depends(get_session),
) -> list[StoryPage]:
    _get_story_draft_or_404(session, story_draft_id)
    statement = (
        select(StoryPage)
        .where(StoryPage.story_draft_id == story_draft_id)
        .order_by(StoryPage.page_number)
    )
    return list(session.exec(statement).all())


@router.post(
    "/generate-plan",
    response_model=IllustrationPlanBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a page-by-page illustration plan for an approved story draft",
)
def generate_illustration_plan(
    payload: IllustrationPlanGenerateRequest,
    session: Session = Depends(get_session),
) -> IllustrationPlanBatchResponse:
    story_draft = _get_story_draft_or_404(session, payload.story_draft_id)
    if story_draft.review_status != "approved_for_illustration":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Story draft must be approved_for_illustration before planning pages",
        )

    # Safe regeneration rule: replace any existing page plan for this draft.
    existing_pages = session.exec(
        select(StoryPage).where(StoryPage.story_draft_id == story_draft.id)
    ).all()
    for page in existing_pages:
        existing_illustrations = session.exec(
            select(Illustration).where(Illustration.story_page_id == page.id)
        ).all()
        for illustration in existing_illustrations:
            session.delete(illustration)
        session.delete(page)
    session.commit()

    page_payloads = generate_story_page_payloads(
        story_draft=story_draft,
        story_idea=session.get(StoryIdea, story_draft.story_idea_id) if story_draft.story_idea_id is not None else None,
        target_page_count=payload.target_page_count,
        min_pages=payload.min_pages,
        max_pages=payload.max_pages,
    )

    created_pages: list[StoryPage] = []
    for item in page_payloads:
        story_page = StoryPage(**item)
        session.add(story_page)
        created_pages.append(story_page)

    session.commit()
    for page in created_pages:
        session.refresh(page)

    return IllustrationPlanBatchResponse(
        story_draft_id=story_draft.id,
        created_count=len(created_pages),
        pages=created_pages,
    )


@router.get("", response_model=list[StoryPageRead], summary="List story page plans")
def list_story_pages(
    story_draft_id: int | None = Query(default=None),
    image_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
) -> list[StoryPage]:
    statement = select(StoryPage).order_by(StoryPage.story_draft_id, StoryPage.page_number).limit(limit)
    if story_draft_id is not None:
        statement = statement.where(StoryPage.story_draft_id == story_draft_id)
    if image_status:
        _validate_image_status(image_status)
        statement = statement.where(StoryPage.image_status == image_status)
    return list(session.exec(statement).all())


@router.post(
    "",
    response_model=StoryPageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create one page plan manually",
)
def create_story_page(
    payload: StoryPageCreate,
    session: Session = Depends(get_session),
) -> StoryPage:
    _get_story_draft_or_404(session, payload.story_draft_id)
    _validate_image_status(payload.image_status)
    story_page = StoryPage.model_validate(payload)
    return _persist_story_page(session, story_page)


@router.get("/{page_id}", response_model=StoryPageRead, summary="Get one story page plan by id")
def get_story_page(page_id: int, session: Session = Depends(get_session)) -> StoryPage:
    return _get_story_page_or_404(session, page_id)


@router.patch(
    "/{page_id}",
    response_model=StoryPageRead,
    summary="Partially update one story page plan",
)
def update_story_page(
    page_id: int,
    payload: StoryPageUpdate,
    session: Session = Depends(get_session),
) -> StoryPage:
    story_page = _get_story_page_or_404(session, page_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "story_draft_id" in update_data and update_data["story_draft_id"] is not None:
        _get_story_draft_or_404(session, update_data["story_draft_id"])
    if "image_status" in update_data and update_data["image_status"] is not None:
        _validate_image_status(update_data["image_status"])

    for field_name, value in update_data.items():
        setattr(story_page, field_name, value)

    story_page.updated_at = utc_now()
    return _persist_story_page(session, story_page)


@router.delete(
    "/{page_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one story page plan",
)
def delete_story_page(page_id: int, session: Session = Depends(get_session)) -> Response:
    story_page = _get_story_page_or_404(session, page_id)
    session.delete(story_page)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
