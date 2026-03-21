from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaintenanceJobCreate(BaseModel):
    key: str
    title: str
    description: str | None = None
    job_type: str
    target_scope: str | None = None
    parameters_json: str | None = None


class MaintenanceJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    description: str | None = None
    job_type: str
    status: str
    target_scope: str | None = None
    parameters_json: str | None = None
    result_json: str | None = None
    error_message: str | None = None
    created_by_user_id: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MaintenanceJobUpdate(BaseModel):
    status: str | None = None
    result_json: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class MaintenanceJobRunResponse(BaseModel):
    job: MaintenanceJobRead
