from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.family_digest_schema import (
    FamilyDigestDetailResponse,
    FamilyDigestGenerateResponse,
    FamilyDigestRead,
    FamilyDigestSummaryCardResponse,
)
from app.services.analytics_service import track_event_safe
from app.services.family_digest_service import (
    generate_weekly_family_digest,
    get_family_digest_detail,
    get_family_digest_summary_card,
    get_or_generate_latest_family_digest,
    list_family_digest_history_for_user,
)
from app.services.user_service import get_user_by_id
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/family-digest", tags=["family-digest"])
admin_router = APIRouter(prefix="/admin/family-digest", tags=["admin-family-digest"])


def _track_family_digest_generated(
    session: Session,
    *,
    user: User,
    digest_id: int,
    period_start: str,
    period_end: str,
) -> None:
    track_event_safe(
        session,
        event_name="family_digest_generated",
        user=user,
        metadata={
            "digest_id": digest_id,
            "period_start": period_start,
            "period_end": period_end,
        },
    )


@router.get("/me/latest", response_model=FamilyDigestDetailResponse, summary="Get or lazily generate the latest family digest")
def get_my_latest_family_digest(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> FamilyDigestDetailResponse:
    digest, child_summaries, generated_now = get_or_generate_latest_family_digest(session, user=current_user)
    if generated_now:
        _track_family_digest_generated(
            session,
            user=current_user,
            digest_id=digest.id,
            period_start=digest.period_start.isoformat(),
            period_end=digest.period_end.isoformat(),
        )
    track_event_safe(
        session,
        event_name="family_digest_viewed",
        user=current_user,
        metadata={"digest_id": digest.id, "generated_now": generated_now},
    )
    return FamilyDigestDetailResponse(digest=digest, child_summaries=child_summaries)


@router.get("/me/summary-card", response_model=FamilyDigestSummaryCardResponse, summary="Get the latest family digest summary card")
def get_my_family_digest_summary_card(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> FamilyDigestSummaryCardResponse:
    response, generated_now = get_family_digest_summary_card(session, user=current_user)
    if generated_now:
        digest, _, _ = get_or_generate_latest_family_digest(session, user=current_user)
        _track_family_digest_generated(
            session,
            user=current_user,
            digest_id=digest.id,
            period_start=digest.period_start.isoformat(),
            period_end=digest.period_end.isoformat(),
        )
    track_event_safe(
        session,
        event_name="family_digest_summary_card_viewed",
        user=current_user,
        metadata={
            "period_start": response.period_start.isoformat(),
            "period_end": response.period_end.isoformat(),
            "stories_completed": response.stories_completed,
            "achievements_earned": response.achievements_earned,
            "generated_now": generated_now,
        },
    )
    return response


@router.get("/me/history", response_model=list[FamilyDigestRead], summary="List recent family digests")
def get_my_family_digest_history(
    limit: int = Query(default=12, ge=1, le=24),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[FamilyDigestRead]:
    return list_family_digest_history_for_user(session, user_id=current_user.id, limit=limit)


@router.get("/me/{digest_id}", response_model=FamilyDigestDetailResponse, summary="Get one family digest")
def get_my_family_digest(
    digest_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> FamilyDigestDetailResponse:
    digest, child_summaries = get_family_digest_detail(session, digest_id=digest_id, user=current_user)
    track_event_safe(
        session,
        event_name="family_digest_viewed",
        user=current_user,
        metadata={"digest_id": digest.id, "generated_now": False},
    )
    return FamilyDigestDetailResponse(digest=digest, child_summaries=child_summaries)


@router.post("/me/generate", response_model=FamilyDigestGenerateResponse, summary="Generate or refresh the latest family digest")
def generate_my_family_digest(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> FamilyDigestGenerateResponse:
    digest, child_summaries, generated_now = generate_weekly_family_digest(
        session,
        user=current_user,
        force_regenerate=True,
    )
    _track_family_digest_generated(
        session,
        user=current_user,
        digest_id=digest.id,
        period_start=digest.period_start.isoformat(),
        period_end=digest.period_end.isoformat(),
    )
    return FamilyDigestGenerateResponse(
        digest=digest,
        child_summaries=child_summaries,
        generated_now=generated_now,
    )


@admin_router.post("/users/{user_id}/generate", response_model=FamilyDigestGenerateResponse, summary="Admin generate a family digest for one user")
def admin_generate_family_digest(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> FamilyDigestGenerateResponse:
    target_user = get_user_by_id(session, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    digest, child_summaries, generated_now = generate_weekly_family_digest(
        session,
        user=target_user,
        force_regenerate=True,
    )
    _track_family_digest_generated(
        session,
        user=target_user,
        digest_id=digest.id,
        period_start=digest.period_start.isoformat(),
        period_end=digest.period_end.isoformat(),
    )
    return FamilyDigestGenerateResponse(
        digest=digest,
        child_summaries=child_summaries,
        generated_now=generated_now,
    )
