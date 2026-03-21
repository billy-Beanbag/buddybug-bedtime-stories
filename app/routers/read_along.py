from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.read_along_schema import (
    ReadAlongDetailResponse,
    ReadAlongJoinRequest,
    ReadAlongJoinResponse,
    ReadAlongSessionCreate,
    ReadAlongSessionRead,
    ReadAlongSessionUpdate,
)
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.read_along_service import (
    create_read_along_session,
    end_read_along_session,
    get_read_along_detail,
    join_read_along_session,
    list_read_along_sessions_for_user,
    update_read_along_session,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/read-along", tags=["read-along"])


@router.get("/me", response_model=list[ReadAlongSessionRead], summary="List my read-along sessions")
def list_my_read_along_sessions(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[ReadAlongSessionRead]:
    return list_read_along_sessions_for_user(
        session,
        current_user=current_user,
        status_filter=status_filter,
        limit=limit,
    )


@router.post(
    "/sessions",
    response_model=ReadAlongDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a read-along session",
)
def post_read_along_session(
    payload: ReadAlongSessionCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadAlongDetailResponse:
    read_along_session, participants = create_read_along_session(
        session,
        current_user=current_user,
        book_id=payload.book_id,
        child_profile_id=payload.child_profile_id,
        language=payload.language,
        current_page_number=payload.current_page_number,
        playback_state=payload.playback_state,
    )
    track_event_safe(
        session,
        event_name="read_along_session_created",
        user=current_user,
        child_profile_id=payload.child_profile_id,
        book_id=payload.book_id,
        metadata={"read_along_session_id": read_along_session.id},
    )
    create_audit_log(
        session,
        action_type="read_along_session_created",
        entity_type="read_along_session",
        entity_id=str(read_along_session.id),
        summary=f"Created read-along session {read_along_session.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": payload.book_id, "child_profile_id": payload.child_profile_id},
    )
    return ReadAlongDetailResponse(session=read_along_session, participants=participants)


@router.get("/sessions/{session_id}", response_model=ReadAlongDetailResponse, summary="Get read-along session detail")
def get_read_along_session_detail(
    session_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadAlongDetailResponse:
    read_along_session, participants = get_read_along_detail(session, session_id=session_id, current_user=current_user)
    return ReadAlongDetailResponse(session=read_along_session, participants=participants)


@router.patch("/sessions/{session_id}", response_model=ReadAlongSessionRead, summary="Update read-along session")
def patch_read_along_session(
    session_id: int,
    payload: ReadAlongSessionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadAlongSessionRead:
    updated_session = update_read_along_session(
        session,
        session_id=session_id,
        current_user=current_user,
        current_page_number=payload.current_page_number,
        playback_state=payload.playback_state,
        status_value=payload.status,
        ended_at=payload.ended_at,
    )
    if payload.current_page_number is not None:
        track_event_safe(
            session,
            event_name="read_along_page_synced",
            user=current_user,
            child_profile_id=updated_session.child_profile_id,
            book_id=updated_session.book_id,
            metadata={
                "read_along_session_id": updated_session.id,
                "current_page_number": payload.current_page_number,
                "playback_state": payload.playback_state,
            },
        )
    return updated_session


@router.post("/join", response_model=ReadAlongJoinResponse, summary="Join a read-along session by code")
def post_join_read_along_session(
    payload: ReadAlongJoinRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadAlongJoinResponse:
    read_along_session, participant = join_read_along_session(
        session,
        current_user=current_user,
        join_code=payload.join_code,
        child_profile_id=payload.child_profile_id,
    )
    track_event_safe(
        session,
        event_name="read_along_session_joined",
        user=current_user,
        child_profile_id=payload.child_profile_id,
        book_id=read_along_session.book_id,
        metadata={"read_along_session_id": read_along_session.id},
    )
    return ReadAlongJoinResponse(session=read_along_session, participant=participant)


@router.post("/sessions/{session_id}/end", response_model=ReadAlongSessionRead, summary="End a read-along session")
def post_end_read_along_session(
    session_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ReadAlongSessionRead:
    ended_session = end_read_along_session(session, session_id=session_id, current_user=current_user)
    track_event_safe(
        session,
        event_name="read_along_session_ended",
        user=current_user,
        child_profile_id=ended_session.child_profile_id,
        book_id=ended_session.book_id,
        metadata={"read_along_session_id": ended_session.id},
    )
    create_audit_log(
        session,
        action_type="read_along_session_ended",
        entity_type="read_along_session",
        entity_id=str(ended_session.id),
        summary=f"Ended read-along session {ended_session.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": ended_session.book_id},
    )
    return ended_session
