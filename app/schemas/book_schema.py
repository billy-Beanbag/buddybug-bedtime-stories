from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class BookCreate(SQLModel):
    story_draft_id: int
    title: str
    cover_image_url: str | None = None
    age_band: str = "3-7"
    content_lane_key: str | None = "bedtime_3_7"
    language: str = "en"
    published: bool = False
    publication_status: str = "ready"
    audio_available: bool = False


class BookRead(BookCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class BookUpdate(SQLModel):
    story_draft_id: int | None = None
    title: str | None = None
    cover_image_url: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    language: str | None = None
    published: bool | None = None
    publication_status: str | None = None
    audio_available: bool | None = None


class BookPageRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    source_story_page_id: int | None = None
    page_number: int
    text_content: str
    image_url: str | None = None
    layout_type: str
    created_at: datetime
    updated_at: datetime


class BookPageUpdate(SQLModel):
    text_content: str | None = None
    image_url: str | None = None
    layout_type: str | None = None


class BookAssemblyRequest(SQLModel):
    story_draft_id: int
    language: str = "en"
    content_lane_key: str | None = None
    publish_immediately: bool = False
    replace_existing: bool = True


class BookAssemblyResponse(SQLModel):
    book: BookRead
    page_count: int
    pages: list[BookPageRead]


class BookDetailResponse(SQLModel):
    book: BookRead
    pages: list[BookPageRead]
