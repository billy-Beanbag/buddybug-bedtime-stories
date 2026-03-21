from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BetaCohortCreate(BaseModel):
    key: str
    name: str
    description: str | None = None
    is_active: bool = True
    feature_flag_keys: str | None = None
    notes: str | None = None


class BetaCohortRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    description: str | None = None
    is_active: bool
    feature_flag_keys: str | None = None
    notes: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class BetaCohortUpdate(BaseModel):
    key: str | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    feature_flag_keys: str | None = None
    notes: str | None = None


class BetaCohortMembershipCreate(BaseModel):
    user_id: int
    source: str = "admin"
    is_active: bool = True


class BetaCohortMembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    beta_cohort_id: int
    user_id: int
    source: str
    invited_by_user_id: int | None = None
    is_active: bool
    joined_at: datetime
    created_at: datetime
    updated_at: datetime


class BetaCohortMembershipUpdate(BaseModel):
    is_active: bool | None = None


class BetaCohortDetailResponse(BaseModel):
    cohort: BetaCohortRead
    memberships: list[BetaCohortMembershipRead]


class UserBetaAccessResponse(BaseModel):
    user_id: int
    cohorts: list[BetaCohortRead]
    cohort_keys: list[str]
