from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.analytics_schema import (
    AnalyticsEventRead,
    AnalyticsSummaryResponse,
    AnalyticsTrackRequest,
    ExperimentConfigRequest,
    ExperimentVariantResponse,
)
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.analytics_service import (
    assign_experiment_variant,
    get_admin_summary,
    get_funnel_counts,
    get_top_books,
    list_analytics_events,
    track_event,
)
from app.utils.dependencies import get_current_admin_user, get_optional_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])
admin_router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"])


@router.post("/track", response_model=AnalyticsEventRead, summary="Track a product analytics event")
def track_analytics_event(
    payload: AnalyticsTrackRequest,
    x_reader_identifier: str | None = Header(default=None, alias="X-Reader-Identifier"),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> AnalyticsEventRead:
    if payload.child_profile_id is not None:
        if current_user is None:
            raise HTTPException(status_code=401, detail="Authentication required for child profile analytics")
        validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=payload.child_profile_id)
    event = track_event(
        session,
        event_name=payload.event_name,
        user=current_user,
        child_profile_id=payload.child_profile_id,
        reader_identifier=x_reader_identifier,
        book_id=payload.book_id,
        session_id=payload.session_id,
        language=payload.language,
        country=payload.country,
        experiment_key=payload.experiment_key,
        experiment_variant=payload.experiment_variant,
        metadata=payload.metadata,
    )
    return AnalyticsEventRead.model_validate(event)


@router.post("/experiments/assign", response_model=ExperimentVariantResponse, summary="Assign a deterministic experiment variant")
def assign_experiment(
    payload: ExperimentConfigRequest,
    x_reader_identifier: str | None = Header(default=None, alias="X-Reader-Identifier"),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> ExperimentVariantResponse:
    return assign_experiment_variant(
        session,
        experiment_key=payload.experiment_key,
        variants=payload.variants,
        user=current_user,
        reader_identifier=x_reader_identifier,
        sticky=payload.sticky,
    )


@admin_router.get("/summary", response_model=AnalyticsSummaryResponse, summary="Get analytics summary")
def admin_analytics_summary(
    days: int = Query(default=30, ge=1, le=365),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> AnalyticsSummaryResponse:
    return get_admin_summary(session, days=days)


@admin_router.get("/events", response_model=list[AnalyticsEventRead], summary="List analytics events")
def admin_analytics_events(
    event_name: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    book_id: int | None = Query(default=None),
    language: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[AnalyticsEventRead]:
    events = list_analytics_events(
        session,
        event_name=event_name,
        user_id=user_id,
        book_id=book_id,
        language=language,
        limit=limit,
    )
    return [AnalyticsEventRead.model_validate(event) for event in events]


@admin_router.get("/books", summary="Get ranked book analytics")
def admin_book_analytics(
    days: int = Query(default=30, ge=1, le=365),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[dict]:
    return get_top_books(session, days=days, limit=20)


@admin_router.get("/funnel", summary="Get product funnel counts")
def admin_funnel_analytics(
    days: int = Query(default=30, ge=1, le=365),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> dict[str, int]:
    return get_funnel_counts(session, days=days)
