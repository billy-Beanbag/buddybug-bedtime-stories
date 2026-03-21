from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class ContentLaneCreate(SQLModel):
    key: str
    display_name: str
    age_band: str
    description: str | None = None
    tone_rules: str
    writing_rules: str
    illustration_rules: str | None = None
    quality_rules: str | None = None
    is_active: bool = True


class ContentLaneRead(ContentLaneCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ContentLaneUpdate(SQLModel):
    key: str | None = None
    display_name: str | None = None
    age_band: str | None = None
    description: str | None = None
    tone_rules: str | None = None
    writing_rules: str | None = None
    illustration_rules: str | None = None
    quality_rules: str | None = None
    is_active: bool | None = None


class AgeBandSupportResponse(SQLModel):
    supported_age_bands: list[str]
    supported_content_lanes: list[ContentLaneRead]
