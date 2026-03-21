from datetime import datetime

from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class ReaderBookSummary(SQLModel):
    book_id: int
    title: str
    cover_image_url: str | None = None
    age_band: str
    content_lane_key: str | None = None
    language: str
    published: bool
    publication_status: str
    page_count: int


class ReaderPageRead(SQLModel):
    id: int
    book_id: int
    source_story_page_id: int | None = None
    page_number: int
    text_content: str
    image_url: str | None = None
    layout_type: str


class ReaderBookDetail(SQLModel):
    book_id: int
    title: str
    cover_image_url: str | None = None
    age_band: str
    content_lane_key: str | None = None
    language: str
    published: bool
    publication_status: str
    pages: list[ReaderPageRead]


class ReadingProgressCreate(SQLModel):
    reader_identifier: str
    book_id: int
    child_profile_id: int | None = None
    current_page_number: int = Field(default=0, ge=0)
    completed: bool = False


class ReadingProgressUpdate(SQLModel):
    child_profile_id: int | None = None
    current_page_number: int | None = Field(default=None, ge=0)
    completed: bool | None = None


class ReadingProgressRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reader_identifier: str
    book_id: int
    child_profile_id: int | None = None
    current_page_number: int
    completed: bool
    last_opened_at: datetime
    created_at: datetime
    updated_at: datetime


class ContinueReadingResponse(SQLModel):
    book_id: int
    title: str
    cover_image_url: str | None = None
    child_profile_id: int | None = None
    current_page_number: int
    completed: bool
    last_opened_at: datetime
