from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AutomationPolicyConfig(BaseModel):
    allow_auto_generate_ideas: bool = True
    allow_auto_generate_drafts: bool = True
    allow_auto_generate_illustration_plans: bool = False
    allow_auto_generate_page_illustrations: bool = False
    allow_auto_assemble_books: bool = False
    allow_auto_publish: bool = False
    stop_at_review_gate: bool = True
    max_jobs_per_run: int = Field(default=1, ge=1, le=50)


class AutomationScheduleCreate(BaseModel):
    name: str
    schedule_type: str
    cron_expression: str | None = None
    interval_minutes: int | None = Field(default=None, ge=1)
    timezone: str | None = None
    job_type: str
    payload_json: str
    policy: AutomationPolicyConfig | None = None
    is_active: bool = True


class AutomationScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    schedule_type: str
    cron_expression: str | None = None
    interval_minutes: int | None = None
    timezone: str | None = None
    job_type: str
    payload_json: str
    policy_json: str | None = None
    policy: AutomationPolicyConfig | None = None
    is_active: bool
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    last_job_id: int | None = None
    last_run_status: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class AutomationScheduleUpdate(BaseModel):
    name: str | None = None
    schedule_type: str | None = None
    cron_expression: str | None = None
    interval_minutes: int | None = Field(default=None, ge=1)
    timezone: str | None = None
    job_type: str | None = None
    payload_json: str | None = None
    policy_json: str | None = None
    is_active: bool | None = None
    next_run_at: datetime | None = None


class AutomationScheduleRunResponse(BaseModel):
    schedule: AutomationScheduleRead
    queued_job_id: int | None = None
    action: str
    message: str


class AutomationQueueResponse(BaseModel):
    items: list[AutomationScheduleRead]
