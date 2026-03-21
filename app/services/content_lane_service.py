from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import ContentLane
from app.utils.seed_content_lanes import BEDTIME_3_7_LANE_KEY, STORY_ADVENTURES_8_12_LANE_KEY

SUPPORTED_AGE_BANDS = ["3-7", "8-12"]


def get_active_lanes(session: Session) -> list[ContentLane]:
    return list(
        session.exec(select(ContentLane).where(ContentLane.is_active.is_(True)).order_by(ContentLane.age_band, ContentLane.key)).all()
    )


def get_lane_by_key(session: Session, key: str) -> ContentLane | None:
    return session.exec(select(ContentLane).where(ContentLane.key == key)).first()


def get_active_lane_by_key(session: Session, key: str) -> ContentLane:
    lane = get_lane_by_key(session, key)
    if lane is None or not lane.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or inactive content lane")
    return lane


def resolve_content_lane_key(age_band: str | None, content_lane_key: str | None) -> str:
    if content_lane_key:
        return content_lane_key
    if age_band == "8-12":
        return STORY_ADVENTURES_8_12_LANE_KEY
    return BEDTIME_3_7_LANE_KEY


def validate_content_lane_key(session: Session, *, age_band: str | None, content_lane_key: str | None) -> ContentLane:
    resolved_key = resolve_content_lane_key(age_band, content_lane_key)
    lane = get_active_lane_by_key(session, resolved_key)
    if age_band and lane.age_band != age_band:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="content_lane_key does not match the requested age_band",
        )
    return lane


def get_lane_rules(session: Session, *, age_band: str | None, content_lane_key: str | None) -> ContentLane:
    return validate_content_lane_key(session, age_band=age_band, content_lane_key=content_lane_key)
