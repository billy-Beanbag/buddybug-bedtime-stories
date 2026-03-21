from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def validate_user_email(value: str) -> str:
    normalized = value.strip().lower()
    if normalized.count("@") != 1:
        raise ValueError("Email must contain a single @ symbol")
    local_part, domain = normalized.split("@", 1)
    if not local_part or not domain or "." not in domain:
        raise ValueError("Email must look like a valid address")
    return normalized


UserEmail = Annotated[str, AfterValidator(validate_user_email)]


class UserCreate(BaseModel):
    email: UserEmail
    password: str = Field(min_length=8)
    display_name: str | None = None
    country: str | None = None
    language: str = "en"
    accept_terms: bool = True
    accept_privacy: bool = True
    referral_code: str | None = None


class UserLogin(BaseModel):
    email: UserEmail
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: UserEmail
    display_name: str | None = None
    country: str | None = None
    language: str
    is_active: bool
    is_admin: bool
    is_editor: bool
    is_educator: bool
    organization_id: int | None = None
    subscription_tier: str
    subscription_status: str
    subscription_expires_at: datetime | None = None
    trial_ends_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    display_name: str | None = None
    country: str | None = None
    language: str | None = None
    is_active: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
