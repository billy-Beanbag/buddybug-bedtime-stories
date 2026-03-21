from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.discovery_schema import DiscoverySearchResult


class ClassroomSetCreate(BaseModel):
    title: str
    description: str | None = None
    age_band: str | None = None
    language: str | None = None
    is_active: bool = True


class ClassroomSetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: str | None = None
    age_band: str | None = None
    language: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ClassroomSetUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    age_band: str | None = None
    language: str | None = None
    is_active: bool | None = None


class ClassroomSetItemCreate(BaseModel):
    book_id: int
    position: int = 0


class ClassroomSetItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    classroom_set_id: int
    book_id: int
    position: int
    created_at: datetime
    updated_at: datetime


class ClassroomSetDetailResponse(BaseModel):
    classroom_set: ClassroomSetRead
    set_items: list[ClassroomSetItemRead]
    items: list[DiscoverySearchResult]
