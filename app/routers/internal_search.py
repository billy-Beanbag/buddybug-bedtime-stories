from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.internal_search_schema import InternalSearchResponse, QuickActionResponse
from app.services.internal_search_service import get_quick_actions_for_context, search_internal_entities
from app.utils.dependencies import get_current_editor_user

router = APIRouter(prefix="/admin/search", tags=["internal-search"])


@router.get("", response_model=InternalSearchResponse, summary="Search internal entities")
def internal_search(
    q: str = Query(default=""),
    limit_per_group: int = Query(default=5, ge=1, le=10),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> InternalSearchResponse:
    normalized_query = q.strip()
    return InternalSearchResponse(
        query=normalized_query,
        groups=search_internal_entities(session, query=normalized_query, limit_per_group=limit_per_group),
    )


@router.get("/actions", response_model=QuickActionResponse, summary="Get safe quick actions")
def internal_search_actions(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    _: User = Depends(get_current_editor_user),
) -> QuickActionResponse:
    return QuickActionResponse(items=get_quick_actions_for_context(entity_type=entity_type, entity_id=entity_id, query=q))
