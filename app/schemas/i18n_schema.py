from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.reader_schema import ReaderPageRead


class BookTranslationCreate(BaseModel):
    book_id: int
    language: str
    title: str
    description: str | None = None
    published: bool = False


class BookTranslationRead(BookTranslationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class BookTranslationUpdate(BaseModel):
    language: str | None = None
    title: str | None = None
    description: str | None = None
    published: bool | None = None


class BookPageTranslationCreate(BaseModel):
    book_page_id: int
    language: str
    text_content: str


class BookPageTranslationRead(BookPageTranslationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class BookPageTranslationUpdate(BaseModel):
    language: str | None = None
    text_content: str | None = None


class CloneBookToLanguageRequest(BaseModel):
    language: str


class LocalizedReaderBookDetail(BaseModel):
    book_id: int
    language: str
    title: str
    cover_image_url: str | None = None
    age_band: str
    content_lane_key: str | None = None
    published: bool
    publication_status: str
    pages: list[ReaderPageRead]
    story_draft_id: int | None = None
    page_mapping: dict[int, int] | None = None  # page_number -> source_story_page_id for preview review


class SupportedLanguagesResponse(BaseModel):
    supported_ui_languages: list[str]
    supported_content_languages: list[str]
    default_language: str
