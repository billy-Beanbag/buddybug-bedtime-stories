from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParentalControlSettingsCreate(BaseModel):
    bedtime_mode_default: bool = True
    allow_audio_autoplay: bool = False
    allow_8_12_content: bool = False
    allow_premium_voice_content: bool = True
    hide_adventure_content_at_bedtime: bool = True
    max_allowed_age_band: str = "3-7"
    quiet_mode_default: bool = True


class ParentalControlSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    bedtime_mode_default: bool
    allow_audio_autoplay: bool
    allow_8_12_content: bool
    allow_premium_voice_content: bool
    hide_adventure_content_at_bedtime: bool
    max_allowed_age_band: str
    quiet_mode_default: bool
    created_at: datetime
    updated_at: datetime


class ParentalControlSettingsUpdate(BaseModel):
    bedtime_mode_default: bool | None = None
    allow_audio_autoplay: bool | None = None
    allow_8_12_content: bool | None = None
    allow_premium_voice_content: bool | None = None
    hide_adventure_content_at_bedtime: bool | None = None
    max_allowed_age_band: str | None = None
    quiet_mode_default: bool | None = None


class ChildControlOverrideCreate(BaseModel):
    bedtime_mode_enabled: bool | None = None
    allow_audio_autoplay: bool | None = None
    allow_8_12_content: bool | None = None
    allow_premium_voice_content: bool | None = None
    quiet_mode_enabled: bool | None = None
    max_allowed_age_band: str | None = None


class ChildControlOverrideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_profile_id: int
    bedtime_mode_enabled: bool | None = None
    allow_audio_autoplay: bool | None = None
    allow_8_12_content: bool | None = None
    allow_premium_voice_content: bool | None = None
    quiet_mode_enabled: bool | None = None
    max_allowed_age_band: str | None = None
    created_at: datetime
    updated_at: datetime


class ChildControlOverrideUpdate(BaseModel):
    bedtime_mode_enabled: bool | None = None
    allow_audio_autoplay: bool | None = None
    allow_8_12_content: bool | None = None
    allow_premium_voice_content: bool | None = None
    quiet_mode_enabled: bool | None = None
    max_allowed_age_band: str | None = None


class ResolvedParentalControlsResponse(BaseModel):
    user_id: int
    child_profile_id: int | None = None
    bedtime_mode_enabled: bool
    allow_audio_autoplay: bool
    allow_8_12_content: bool
    allow_premium_voice_content: bool
    hide_adventure_content_at_bedtime: bool
    max_allowed_age_band: str
    quiet_mode_enabled: bool
