from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChangelogEntryCreate(BaseModel):
    version_label: str
    title: str
    summary: str
    details_markdown: str | None = None
    audience: str
    status: str = "draft"
    area_tags: str | None = None
    feature_flag_keys: str | None = None
    published_at: datetime | None = None


class ChangelogEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_label: str
    title: str
    summary: str
    details_markdown: str | None = None
    audience: str
    status: str
    area_tags: str | None = None
    feature_flag_keys: str | None = None
    published_at: datetime | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ChangelogEntryUpdate(BaseModel):
    version_label: str | None = None
    title: str | None = None
    summary: str | None = None
    details_markdown: str | None = None
    audience: str | None = None
    status: str | None = None
    area_tags: str | None = None
    feature_flag_keys: str | None = None
    published_at: datetime | None = None
