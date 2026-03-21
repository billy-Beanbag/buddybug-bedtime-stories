from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.reporting_schema import (
    ContentPerformanceResponse,
    EngagementMetricsResponse,
    KPIOverviewResponse,
    SegmentBreakdownResponse,
    SubscriptionMetricsResponse,
    SupportMetricsResponse,
)
from app.services.reporting_service import (
    get_age_band_breakdown,
    get_content_lane_breakdown,
    get_engagement_metrics,
    get_kpi_overview,
    get_language_breakdown,
    get_support_metrics,
    get_subscription_metrics,
    get_top_content_performance,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/reporting", tags=["admin-reporting"])


@router.get("/kpi-overview", response_model=KPIOverviewResponse, summary="Get KPI overview metrics")
def admin_reporting_kpi_overview(
    days: int | None = Query(default=None, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> KPIOverviewResponse:
    return get_kpi_overview(session, days=days, start_date=start_date, end_date=end_date)


@router.get("/engagement", response_model=EngagementMetricsResponse, summary="Get engagement metrics")
def admin_reporting_engagement(
    days: int | None = Query(default=None, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> EngagementMetricsResponse:
    return get_engagement_metrics(session, days=days, start_date=start_date, end_date=end_date)


@router.get("/subscriptions", response_model=SubscriptionMetricsResponse, summary="Get subscription metrics")
def admin_reporting_subscriptions(
    days: int | None = Query(default=None, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> SubscriptionMetricsResponse:
    return get_subscription_metrics(session, days=days, start_date=start_date, end_date=end_date)


@router.get("/content/top", response_model=ContentPerformanceResponse, summary="Get top content performance")
def admin_reporting_top_content(
    limit: int = Query(default=20, ge=1, le=100),
    days: int | None = Query(default=None, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> ContentPerformanceResponse:
    return get_top_content_performance(session, limit=limit, days=days, start_date=start_date, end_date=end_date)


@router.get("/breakdown/languages", response_model=SegmentBreakdownResponse, summary="Get language breakdown")
def admin_reporting_language_breakdown(
    days: int | None = Query(default=None, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> SegmentBreakdownResponse:
    return get_language_breakdown(session, days=days, start_date=start_date, end_date=end_date)


@router.get("/breakdown/age-bands", response_model=SegmentBreakdownResponse, summary="Get age band breakdown")
def admin_reporting_age_band_breakdown(
    days: int | None = Query(default=None, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> SegmentBreakdownResponse:
    return get_age_band_breakdown(session, days=days, start_date=start_date, end_date=end_date)


@router.get("/breakdown/content-lanes", response_model=SegmentBreakdownResponse, summary="Get content lane breakdown")
def admin_reporting_content_lane_breakdown(
    days: int | None = Query(default=None, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> SegmentBreakdownResponse:
    return get_content_lane_breakdown(session, days=days, start_date=start_date, end_date=end_date)


@router.get("/support", response_model=SupportMetricsResponse, summary="Get support metrics")
def admin_reporting_support(
    days: int | None = Query(default=None, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> SupportMetricsResponse:
    return get_support_metrics(session, days=days, start_date=start_date, end_date=end_date)
