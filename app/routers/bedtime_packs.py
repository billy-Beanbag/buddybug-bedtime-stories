from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.bedtime_pack_schema import (
    BedtimePackCreate,
    BedtimePackDetailResponse,
    BedtimePackGenerateResponse,
    BedtimePackItemRead,
    BedtimePackItemUpdate,
    BedtimePackRead,
)
from app.services.analytics_service import track_event_safe
from app.services.bedtime_pack_service import (
    archive_bedtime_pack,
    generate_bedtime_pack,
    get_bedtime_pack_detail,
    get_or_generate_tonight_pack,
    list_bedtime_packs_for_user,
    update_pack_item_status,
    validate_bedtime_pack_access,
)
from app.services.child_profile_service import validate_child_profile_ownership
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/bedtime-packs", tags=["bedtime-packs"])


@router.get("/me/latest", response_model=BedtimePackDetailResponse, summary="Get or lazily generate the latest bedtime pack")
def get_my_latest_bedtime_pack(
    child_profile_id: int | None = Query(default=None),
    date_value: date | None = Query(default=None, alias="date"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BedtimePackDetailResponse:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    pack, items, generated_now = get_or_generate_tonight_pack(
        session,
        user=current_user,
        child_profile_id=child_profile_id,
        target_date=date_value,
    )
    if generated_now:
        track_event_safe(
            session,
            event_name="bedtime_pack_generated",
            user=current_user,
            child_profile_id=pack.child_profile_id,
            metadata={"pack_id": pack.id, "pack_type": pack.pack_type, "active_date": str(pack.active_date)},
        )
    track_event_safe(
        session,
        event_name="bedtime_pack_viewed",
        user=current_user,
        child_profile_id=pack.child_profile_id,
        metadata={"pack_id": pack.id, "generated_now": generated_now},
    )
    return BedtimePackDetailResponse(pack=pack, items=items)


@router.get("/me", response_model=list[BedtimePackRead], summary="List current user bedtime packs")
def list_my_bedtime_packs(
    child_profile_id: int | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[BedtimePackRead]:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    return list_bedtime_packs_for_user(
        session,
        user_id=current_user.id,
        child_profile_id=child_profile_id,
        status_value=status_value,
        limit=limit,
    )


@router.get("/me/{pack_id}", response_model=BedtimePackDetailResponse, summary="Get one bedtime pack")
def get_my_bedtime_pack(
    pack_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BedtimePackDetailResponse:
    pack, items = get_bedtime_pack_detail(session, user=current_user, pack_id=pack_id)
    track_event_safe(
        session,
        event_name="bedtime_pack_viewed",
        user=current_user,
        child_profile_id=pack.child_profile_id,
        metadata={"pack_id": pack.id, "generated_now": False},
    )
    return BedtimePackDetailResponse(pack=pack, items=items)


@router.post("/me/generate", response_model=BedtimePackGenerateResponse, summary="Generate a bedtime pack")
def generate_my_bedtime_pack(
    payload: BedtimePackCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BedtimePackGenerateResponse:
    pack, items, generated_now = generate_bedtime_pack(
        session,
        user=current_user,
        child_profile_id=payload.child_profile_id,
        title=payload.title,
        pack_type=payload.pack_type,
        language=payload.language,
        age_band=payload.age_band,
        content_lane_key=payload.content_lane_key,
        prefer_narration=payload.prefer_narration,
        active_date=payload.active_date,
        force_regenerate=True,
    )
    track_event_safe(
        session,
        event_name="bedtime_pack_generated",
        user=current_user,
        child_profile_id=pack.child_profile_id,
        metadata={"pack_id": pack.id, "pack_type": pack.pack_type, "active_date": str(pack.active_date)},
    )
    return BedtimePackGenerateResponse(pack=pack, items=items, generated_now=generated_now)


@router.patch("/me/{pack_id}/items/{item_id}", response_model=BedtimePackItemRead, summary="Update one bedtime pack item")
def patch_my_bedtime_pack_item(
    pack_id: int,
    item_id: int,
    payload: BedtimePackItemUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BedtimePackItemRead:
    updated_item, pack = update_pack_item_status(
        session,
        user=current_user,
        pack_id=pack_id,
        item_id=item_id,
        completion_status=payload.completion_status,
        recommended_narration=payload.recommended_narration,
    )
    if payload.completion_status == "opened":
        track_event_safe(
            session,
            event_name="bedtime_pack_item_opened",
            user=current_user,
            child_profile_id=pack.child_profile_id,
            book_id=updated_item.book_id,
            metadata={"pack_id": pack.id, "item_id": updated_item.id, "position": updated_item.position},
        )
    if payload.completion_status == "completed":
        track_event_safe(
            session,
            event_name="bedtime_pack_item_completed",
            user=current_user,
            child_profile_id=pack.child_profile_id,
            book_id=updated_item.book_id,
            metadata={"pack_id": pack.id, "item_id": updated_item.id, "position": updated_item.position},
        )
        if pack.status == "completed":
            track_event_safe(
                session,
                event_name="bedtime_pack_completed",
                user=current_user,
                child_profile_id=pack.child_profile_id,
                metadata={"pack_id": pack.id},
            )
    return updated_item


@router.post("/me/{pack_id}/archive", response_model=BedtimePackRead, summary="Archive a bedtime pack")
def archive_my_bedtime_pack(
    pack_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BedtimePackRead:
    validate_bedtime_pack_access(session, user_id=current_user.id, pack_id=pack_id)
    return archive_bedtime_pack(session, user=current_user, pack_id=pack_id)
