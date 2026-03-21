from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LifecycleMilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    milestone_type: str
    occurred_at: datetime
    title: str
    summary: str | None = None
    source_table: str | None = None
    source_id: str | None = None
    metadata_json: str | None = None
    created_at: datetime
    updated_at: datetime


class LifecycleTimelineResponse(BaseModel):
    user_id: int
    milestones: list[LifecycleMilestoneRead]


class LifecycleSummaryResponse(BaseModel):
    user_id: int
    first_seen_at: datetime | None = None
    latest_activity_at: datetime | None = None
    has_completed_onboarding: bool
    has_child_profiles: bool
    has_premium_history: bool
    current_subscription_status: str | None = None
    support_ticket_count: int
    open_billing_recovery: bool
    lifecycle_stage: str | None = None


class LifecycleRebuildResponse(BaseModel):
    user_id: int
    created_count: int
    milestones: list[LifecycleMilestoneRead]
