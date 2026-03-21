from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApiKeyCreate(BaseModel):
    name: str
    scopes: str
    is_active: bool = True


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key_prefix: str
    scopes: str
    is_active: bool
    created_by_user_id: int | None = None
    last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApiKeyCreateResponse(BaseModel):
    key: ApiKeyRead
    raw_api_key: str


class ApiKeyUpdate(BaseModel):
    name: str | None = None
    scopes: str | None = None
    is_active: bool | None = None
