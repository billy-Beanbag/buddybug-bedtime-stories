from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.lifecycle_schema import (
    LifecycleRebuildResponse,
    LifecycleSummaryResponse,
    LifecycleTimelineResponse,
)
from app.services.audit_service import create_audit_log
from app.services.lifecycle_service import (
    get_user_lifecycle_summary,
    get_user_lifecycle_timeline,
    rebuild_user_lifecycle_milestones,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/lifecycle", tags=["admin-lifecycle"])


@router.get("/users/{user_id}", response_model=LifecycleTimelineResponse, summary="Get lifecycle timeline for one user")
def get_lifecycle_timeline(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> LifecycleTimelineResponse:
    return get_user_lifecycle_timeline(session, user_id=user_id)


@router.get("/users/{user_id}/summary", response_model=LifecycleSummaryResponse, summary="Get lifecycle summary for one user")
def get_lifecycle_summary(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> LifecycleSummaryResponse:
    return get_user_lifecycle_summary(session, user_id=user_id)


@router.post("/users/{user_id}/rebuild", response_model=LifecycleRebuildResponse, summary="Rebuild lifecycle milestones for one user")
def rebuild_lifecycle(
    user_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> LifecycleRebuildResponse:
    response = rebuild_user_lifecycle_milestones(session, user_id=user_id)
    create_audit_log(
        session,
        action_type="lifecycle_rebuild_run",
        entity_type="lifecycle_timeline",
        entity_id=str(user_id),
        summary=f"Rebuilt lifecycle milestones for user {user_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"created_count": response.created_count},
    )
    return response
