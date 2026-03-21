from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import ContentLane, User
from app.schemas.content_lane_schema import (
    AgeBandSupportResponse,
    ContentLaneCreate,
    ContentLaneRead,
    ContentLaneUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.content_lane_service import SUPPORTED_AGE_BANDS, get_active_lanes, get_lane_by_key
from app.services.review_service import utc_now
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/content-lanes", tags=["content-lanes"])


def _persist_lane(session: Session, lane: ContentLane) -> ContentLane:
    session.add(lane)
    session.commit()
    session.refresh(lane)
    return lane


def _get_lane_or_404(session: Session, lane_id: int) -> ContentLane:
    lane = session.get(ContentLane, lane_id)
    if lane is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content lane not found")
    return lane


@router.get("", response_model=list[ContentLaneRead], summary="List active content lanes")
def list_content_lanes(session: Session = Depends(get_session)) -> list[ContentLane]:
    return get_active_lanes(session)


@router.get("/support", response_model=AgeBandSupportResponse, summary="Get supported age bands and content lanes")
def get_content_lane_support(session: Session = Depends(get_session)) -> AgeBandSupportResponse:
    lanes = get_active_lanes(session)
    return AgeBandSupportResponse(
        supported_age_bands=SUPPORTED_AGE_BANDS,
        supported_content_lanes=[ContentLaneRead.model_validate(lane) for lane in lanes],
    )


@router.post("", response_model=ContentLaneRead, status_code=status.HTTP_201_CREATED, summary="Create a content lane")
def create_content_lane(
    payload: ContentLaneCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> ContentLane:
    if get_lane_by_key(session, payload.key) is not None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content lane key already exists")
    lane = ContentLane.model_validate(payload)
    lane = _persist_lane(session, lane)
    create_audit_log(
        session,
        action_type="content_lane_created",
        entity_type="content_lane",
        entity_id=str(lane.id),
        summary=f"Created content lane '{lane.key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"age_band": lane.age_band},
    )
    return lane


@router.patch("/{lane_id}", response_model=ContentLaneRead, summary="Update a content lane")
def update_content_lane(
    lane_id: int,
    payload: ContentLaneUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> ContentLane:
    lane = _get_lane_or_404(session, lane_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "key" in update_data and update_data["key"] != lane.key:
        existing = get_lane_by_key(session, update_data["key"])
        if existing is not None:
            from fastapi import HTTPException

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content lane key already exists")
    for field_name, value in update_data.items():
        setattr(lane, field_name, value)
    lane.updated_at = utc_now()
    lane = _persist_lane(session, lane)
    create_audit_log(
        session,
        action_type="content_lane_updated",
        entity_type="content_lane",
        entity_id=str(lane.id),
        summary=f"Updated content lane '{lane.key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"age_band": lane.age_band, "is_active": lane.is_active},
    )
    return lane


@router.delete("/{lane_id}", response_model=ContentLaneRead, summary="Deactivate a content lane")
def deactivate_content_lane(
    lane_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> ContentLane:
    lane = _get_lane_or_404(session, lane_id)
    lane.is_active = False
    lane.updated_at = utc_now()
    lane = _persist_lane(session, lane)
    create_audit_log(
        session,
        action_type="content_lane_deactivated",
        entity_type="content_lane",
        entity_id=str(lane.id),
        summary=f"Deactivated content lane '{lane.key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"age_band": lane.age_band},
    )
    return lane
