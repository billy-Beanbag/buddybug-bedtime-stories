from datetime import datetime

from pydantic import BaseModel


class KPIOverviewResponse(BaseModel):
    total_users: int
    active_users_30d: int
    total_child_profiles: int
    active_child_profiles_30d: int
    total_premium_users: int
    premium_conversion_rate: float
    total_published_books: int
    total_saved_library_items: int
    total_downloads: int
    total_support_tickets_open: int
    generated_at: datetime


class EngagementMetricsResponse(BaseModel):
    book_opens_30d: int
    book_completions_30d: int
    book_replays_30d: int
    narration_starts_30d: int
    narration_completions_30d: int
    daily_story_views_30d: int
    avg_completion_rate_30d: float


class SubscriptionMetricsResponse(BaseModel):
    free_users: int
    premium_users: int
    trialing_users: int
    canceled_users: int
    active_conversion_rate: float
    checkout_started_30d: int
    checkout_completed_30d: int


class ContentPerformanceItem(BaseModel):
    book_id: int
    title: str
    language: str
    age_band: str
    content_lane_key: str | None = None
    opens: int
    completions: int
    replays: int
    downloads: int
    narration_starts: int


class ContentPerformanceResponse(BaseModel):
    items: list[ContentPerformanceItem]


class SegmentBreakdownItem(BaseModel):
    key: str
    count: int


class SegmentBreakdownResponse(BaseModel):
    items: list[SegmentBreakdownItem]


class SupportMetricsResponse(BaseModel):
    open_tickets: int
    in_progress_tickets: int
    resolved_30d: int
    avg_resolution_hours: float | None
