from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HousekeepingPolicyCreate(BaseModel):
    key: str
    name: str
    target_table: str
    action_type: str
    retention_days: int
    enabled: bool = True
    dry_run_only: bool = True
    notes: str | None = None


class HousekeepingPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    target_table: str
    action_type: str
    retention_days: int
    enabled: bool
    dry_run_only: bool
    notes: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class HousekeepingPolicyUpdate(BaseModel):
    key: str | None = None
    name: str | None = None
    target_table: str | None = None
    action_type: str | None = None
    retention_days: int | None = None
    enabled: bool | None = None
    dry_run_only: bool | None = None
    notes: str | None = None


class HousekeepingRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_id: int
    status: str
    dry_run: bool
    candidate_count: int
    affected_count: int
    result_json: str | None = None
    error_message: str | None = None
    created_by_user_id: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class HousekeepingRunResponse(BaseModel):
    run: HousekeepingRunRead


class HousekeepingSummaryResponse(BaseModel):
    policies: list[HousekeepingPolicyRead]
    recent_runs: list[HousekeepingRunRead]
