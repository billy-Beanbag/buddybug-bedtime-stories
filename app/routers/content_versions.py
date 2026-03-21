from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.content_version_schema import RollbackResponse, StoryDraftVersionRead, StoryPageVersionRead
from app.services.audit_service import create_audit_log
from app.services.content_version_service import (
    get_story_draft_version_or_404,
    get_story_page_version_or_404,
    list_story_draft_versions,
    list_story_page_versions,
    rollback_story_draft,
    rollback_story_page,
)
from app.services.editorial_service import get_editorial_draft_or_404, get_editorial_story_page_or_404
from app.utils.dependencies import get_current_editor_user

router = APIRouter(prefix="/content-versions", tags=["content-versions"])


@router.get("/story-drafts/{draft_id}", response_model=list[StoryDraftVersionRead], summary="List story draft versions")
def get_story_draft_version_history(
    draft_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[StoryDraftVersionRead]:
    get_editorial_draft_or_404(session, draft_id)
    return list_story_draft_versions(session, draft_id=draft_id)


@router.get("/story-pages/{page_id}", response_model=list[StoryPageVersionRead], summary="List story page versions")
def get_story_page_version_history(
    page_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[StoryPageVersionRead]:
    get_editorial_story_page_or_404(session, page_id)
    return list_story_page_versions(session, page_id=page_id)


@router.post(
    "/story-drafts/{draft_id}/rollback/{version_id}",
    response_model=RollbackResponse,
    summary="Rollback story draft to a previous version",
)
def rollback_story_draft_route(
    draft_id: int,
    version_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> RollbackResponse:
    draft = get_editorial_draft_or_404(session, draft_id)
    version = get_story_draft_version_or_404(session, version_id=version_id)
    rollback_story_draft(session, story_draft=draft, version=version, created_by_user_id=current_user.id)
    create_audit_log(
        session,
        action_type="story_draft_rolled_back",
        entity_type="story_draft",
        entity_id=str(draft.id),
        summary=f"Rolled back story draft '{draft.title}' to version {version.version_number}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"version_id": version.id, "version_number": version.version_number},
    )
    return RollbackResponse(
        message=f"Story draft rolled back to version {version.version_number}",
        entity_type="story_draft",
        entity_id=draft.id,
        rolled_back_to_version_id=version.id,
    )


@router.post(
    "/story-pages/{page_id}/rollback/{version_id}",
    response_model=RollbackResponse,
    summary="Rollback story page to a previous version",
)
def rollback_story_page_route(
    page_id: int,
    version_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> RollbackResponse:
    page = get_editorial_story_page_or_404(session, page_id)
    version = get_story_page_version_or_404(session, version_id=version_id)
    rollback_story_page(session, story_page=page, version=version, created_by_user_id=current_user.id)
    create_audit_log(
        session,
        action_type="story_page_rolled_back",
        entity_type="story_page",
        entity_id=str(page.id),
        summary=f"Rolled back story page {page.page_number} to version {version.version_number}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"version_id": version.id, "version_number": version.version_number},
    )
    return RollbackResponse(
        message=f"Story page rolled back to version {version.version_number}",
        entity_type="story_page",
        entity_id=page.id,
        rolled_back_to_version_id=version.id,
    )
