from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BedtimePackCreate(BaseModel):
    child_profile_id: int | None = None
    title: str | None = None
    pack_type: str = "nightly"
    language: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    prefer_narration: bool = False
    active_date: date | None = None


class BedtimePackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    child_profile_id: int | None = None
    title: str
    description: str | None = None
    status: str
    pack_type: str
    language: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    prefer_narration: bool
    generated_reason: str | None = None
    active_date: date | None = None
    created_at: datetime
    updated_at: datetime


class BedtimePackItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bedtime_pack_id: int
    book_id: int
    position: int
    recommended_narration: bool
    completion_status: str
    created_at: datetime
    updated_at: datetime


class BedtimePackItemUpdate(BaseModel):
    completion_status: str | None = None
    recommended_narration: bool | None = None


class BedtimePackDetailResponse(BaseModel):
    pack: BedtimePackRead
    items: list[BedtimePackItemRead]


class BedtimePackGenerateResponse(BaseModel):
    pack: BedtimePackRead
    items: list[BedtimePackItemRead]
    generated_now: bool
