from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookDiscoveryMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    searchable_title: str
    searchable_summary: str | None = None
    searchable_text: str | None = None
    age_band: str
    language: str
    content_lane_key: str | None = None
    tone_tags: str | None = None
    theme_tags: str | None = None
    character_tags: str | None = None
    setting_tags: str | None = None
    style_tags: str | None = None
    bedtime_safe: bool
    adventure_level: str | None = None
    is_featured: bool
    created_at: datetime
    updated_at: datetime


class BookDiscoveryMetadataUpdate(BaseModel):
    searchable_title: str | None = None
    searchable_summary: str | None = None
    searchable_text: str | None = None
    age_band: str | None = None
    language: str | None = None
    content_lane_key: str | None = None
    tone_tags: str | None = None
    theme_tags: str | None = None
    character_tags: str | None = None
    setting_tags: str | None = None
    style_tags: str | None = None
    bedtime_safe: bool | None = None
    adventure_level: str | None = None
    is_featured: bool | None = None


class BookCollectionCreate(BaseModel):
    key: str
    title: str
    description: str | None = None
    language: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    is_public: bool = True
    is_featured: bool = False


class BookCollectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    description: str | None = None
    language: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    is_public: bool
    is_featured: bool
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class BookCollectionUpdate(BaseModel):
    key: str | None = None
    title: str | None = None
    description: str | None = None
    language: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    is_public: bool | None = None
    is_featured: bool | None = None


class BookCollectionItemCreate(BaseModel):
    book_id: int
    position: int = 0


class BookCollectionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    collection_id: int
    book_id: int
    position: int
    created_at: datetime
    updated_at: datetime


class BookCollectionItemUpdate(BaseModel):
    position: int | None = None


class DiscoverySearchRequest(BaseModel):
    q: str | None = None
    age_band: str | None = None
    language: str | None = None
    content_lane_key: str | None = None
    tone_tag: str | None = None
    character_tag: str | None = None
    bedtime_safe: bool | None = None
    featured_only: bool = False
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class DiscoverySearchResult(BaseModel):
    book_id: int
    title: str
    cover_image_url: str | None = None
    age_band: str
    language: str
    content_lane_key: str | None = None
    published: bool
    publication_status: str
    score: float | None = None
    reasons: list[str] | None = None


class DiscoverySearchResponse(BaseModel):
    total: int
    items: list[DiscoverySearchResult]


class CollectionDetailResponse(BaseModel):
    collection: BookCollectionRead
    items: list[DiscoverySearchResult]
