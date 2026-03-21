from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.activity_feed_schema import ActivityFeedResponse
from app.services.activity_feed_service import get_entity_activity_feed, get_user_activity_feed
from app.utils.dependencies import get_current_editor_user

router = APIRouter(prefix="/admin/activity", tags=["activity-feed"])


@router.get("/entity/{entity_type}/{entity_id}", response_model=ActivityFeedResponse, summary="Get one entity activity feed")
def get_entity_timeline(
    entity_type: str,
    entity_id: int,
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> ActivityFeedResponse:
    return get_entity_activity_feed(session, entity_type=entity_type, entity_id=entity_id, limit=limit)


@router.get("/users/{user_id}", response_model=ActivityFeedResponse, summary="Get one user activity feed")
def get_user_timeline(
    user_id: int,
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> ActivityFeedResponse:
    return get_user_activity_feed(session, user_id=user_id, limit=limit)
