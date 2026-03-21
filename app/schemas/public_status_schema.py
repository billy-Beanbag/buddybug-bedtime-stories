from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PublicStatusComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    description: str | None = None
    sort_order: int
    is_active: bool
    current_status: str
    created_at: datetime
    updated_at: datetime


class PublicStatusComponentUpdate(BaseModel):
    current_status: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    description: str | None = None
    name: str | None = None


class PublicStatusNoticeCreate(BaseModel):
    title: str
    summary: str
    notice_type: str
    public_status: str
    component_key: str | None = None
    linked_incident_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True
    is_public: bool = True


class PublicStatusNoticeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str
    notice_type: str
    public_status: str
    component_key: str | None = None
    linked_incident_id: int | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    is_active: bool
    is_public: bool
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class PublicStatusNoticeUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    notice_type: str | None = None
    public_status: str | None = None
    component_key: str | None = None
    linked_incident_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None
    is_public: bool | None = None


class PublicStatusPageResponse(BaseModel):
    overall_status: str
    components: list[PublicStatusComponentRead]
    active_notices: list[PublicStatusNoticeRead]
    upcoming_maintenance: list[PublicStatusNoticeRead]
