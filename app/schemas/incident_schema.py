from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentRecordCreate(BaseModel):
    title: str
    summary: str
    severity: str
    status: str = "investigating"
    affected_area: str
    feature_flag_key: str | None = None
    assigned_to_user_id: int | None = None
    started_at: datetime | None = None
    detected_at: datetime | None = None
    customer_impact_summary: str | None = None


class IncidentRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str
    severity: str
    status: str
    affected_area: str
    feature_flag_key: str | None = None
    assigned_to_user_id: int | None = None
    started_at: datetime
    detected_at: datetime | None = None
    mitigated_at: datetime | None = None
    resolved_at: datetime | None = None
    customer_impact_summary: str | None = None
    root_cause_summary: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class IncidentRecordUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    severity: str | None = None
    status: str | None = None
    affected_area: str | None = None
    feature_flag_key: str | None = None
    assigned_to_user_id: int | None = None
    detected_at: datetime | None = None
    mitigated_at: datetime | None = None
    resolved_at: datetime | None = None
    customer_impact_summary: str | None = None
    root_cause_summary: str | None = None


class IncidentUpdateCreate(BaseModel):
    update_type: str
    body: str


class IncidentUpdateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    author_user_id: int | None = None
    update_type: str
    body: str
    created_at: datetime
    updated_at: datetime


class IncidentResolveRequest(BaseModel):
    body: str | None = None


class IncidentDetailResponse(BaseModel):
    incident: IncidentRecordRead
    updates: list[IncidentUpdateRead]


class IncidentSummaryResponse(BaseModel):
    open_incidents: int
    sev_1_open: int
    sev_2_open: int
    incidents_resolved_30d: int


class RunbookEntryCreate(BaseModel):
    key: str
    title: str
    area: str
    summary: str
    steps_markdown: str
    is_active: bool = True


class RunbookEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    area: str
    summary: str
    steps_markdown: str
    is_active: bool
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class RunbookEntryUpdate(BaseModel):
    key: str | None = None
    title: str | None = None
    area: str | None = None
    summary: str | None = None
    steps_markdown: str | None = None
    is_active: bool | None = None
