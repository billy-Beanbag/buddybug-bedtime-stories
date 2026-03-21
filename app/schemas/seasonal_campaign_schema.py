from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.discovery_schema import DiscoverySearchResult


class SeasonalCampaignCreate(BaseModel):
    key: str
    title: str
    description: str | None = None
    start_at: datetime
    end_at: datetime
    is_active: bool = True
    language: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    homepage_badge_text: str | None = None
    homepage_cta_label: str | None = None
    homepage_cta_route: str | None = None
    banner_style_key: str | None = None


class SeasonalCampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    description: str | None = None
    start_at: datetime
    end_at: datetime
    is_active: bool
    language: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    homepage_badge_text: str | None = None
    homepage_cta_label: str | None = None
    homepage_cta_route: str | None = None
    banner_style_key: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class SeasonalCampaignUpdate(BaseModel):
    key: str | None = None
    title: str | None = None
    description: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    is_active: bool | None = None
    language: str | None = None
    age_band: str | None = None
    content_lane_key: str | None = None
    homepage_badge_text: str | None = None
    homepage_cta_label: str | None = None
    homepage_cta_route: str | None = None
    banner_style_key: str | None = None


class SeasonalCampaignItemCreate(BaseModel):
    book_id: int
    position: int = 0


class SeasonalCampaignItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    book_id: int
    position: int
    created_at: datetime
    updated_at: datetime


class SeasonalCampaignDetailResponse(BaseModel):
    campaign: SeasonalCampaignRead
    items: list[DiscoverySearchResult]
