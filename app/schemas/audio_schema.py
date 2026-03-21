from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NarrationVoiceCreate(BaseModel):
    key: str
    display_name: str
    description: str | None = None
    language: str = "en"
    accent: str | None = None
    gender_style: str | None = None
    age_style: str | None = None
    tone_style: str | None = None
    is_active: bool = True


class NarrationVoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    display_name: str
    description: str | None = None
    language: str
    accent: str | None = None
    gender_style: str | None = None
    age_style: str | None = None
    tone_style: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NarrationVoiceUpdate(BaseModel):
    key: str | None = None
    display_name: str | None = None
    description: str | None = None
    language: str | None = None
    accent: str | None = None
    gender_style: str | None = None
    age_style: str | None = None
    tone_style: str | None = None
    is_active: bool | None = None


class BookAudioCreate(BaseModel):
    book_id: int
    voice_id: int
    script_source: str = "assembled_book_text"
    script_text: str
    audio_url: str
    duration_seconds: int | None = None
    provider: str = "manual_upload"
    provider_audio_id: str | None = None
    version_number: int = 1
    approval_status: str = "generated"
    is_active: bool = False
    generation_notes: str | None = None


class BookAudioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    voice_id: int
    script_source: str
    script_text: str
    audio_url: str
    duration_seconds: int | None = None
    provider: str
    provider_audio_id: str | None = None
    version_number: int
    approval_status: str
    is_active: bool
    generation_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class BookAudioUpdate(BaseModel):
    book_id: int | None = None
    voice_id: int | None = None
    script_source: str | None = None
    script_text: str | None = None
    audio_url: str | None = None
    duration_seconds: int | None = None
    provider: str | None = None
    provider_audio_id: str | None = None
    version_number: int | None = None
    approval_status: str | None = None
    is_active: bool | None = None
    generation_notes: str | None = None


class BookAudioGenerateRequest(BaseModel):
    book_id: int
    voice_id: int
    script_source: str = "assembled_book_text"
    generation_notes: str | None = None
    replace_active_for_voice: bool = False


class BookAudioGenerateResponse(BaseModel):
    audio: BookAudioRead
    book_id: int
    voice_id: int


class BookAudioApprovalRequest(BaseModel):
    generation_notes: str | None = None
    make_active: bool = True


class ReaderAudioSummary(BaseModel):
    id: int
    book_id: int
    voice_id: int
    voice_key: str
    voice_display_name: str
    language: str
    audio_url: str
    duration_seconds: int | None = None
    is_active: bool
    approval_status: str
