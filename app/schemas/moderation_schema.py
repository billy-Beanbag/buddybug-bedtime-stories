from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ModerationCaseCreate(BaseModel):
    case_type: str
    target_type: str
    target_id: int | None = None
    source_type: str
    source_id: int | None = None
    severity: str
    status: str = "open"
    summary: str
    notes: str | None = None
    assigned_to_user_id: int | None = None


class ModerationCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_type: str
    target_type: str
    target_id: int | None = None
    source_type: str
    source_id: int | None = None
    severity: str
    status: str
    summary: str
    notes: str | None = None
    assigned_to_user_id: int | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None


class ModerationCaseUpdate(BaseModel):
    severity: str | None = None
    status: str | None = None
    summary: str | None = None
    notes: str | None = None
    assigned_to_user_id: int | None = None
    resolved_at: datetime | None = None


class ModerationCaseDetailResponse(BaseModel):
    case: ModerationCaseRead
    target_summary: str | None = None
    source_summary: str | None = None
