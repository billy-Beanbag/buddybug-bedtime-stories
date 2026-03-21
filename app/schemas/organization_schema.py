from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganizationCreate(BaseModel):
    name: str
    slug: str
    is_active: bool = True


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OrganizationUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_active: bool | None = None


class OrganizationMembershipCreate(BaseModel):
    user_id: int
    role: str
    is_active: bool = True


class OrganizationMembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    user_id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OrganizationMembershipUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class OrganizationDetailResponse(BaseModel):
    organization: OrganizationRead
    memberships: list[OrganizationMembershipRead]
