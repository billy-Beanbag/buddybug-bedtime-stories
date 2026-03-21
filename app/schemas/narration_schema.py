from pydantic import BaseModel, ConfigDict


class NarrationVoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    display_name: str
    language: str
    style: str | None = None
    description: str | None = None
    is_premium: bool


class BookNarrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    language: str
    narration_voice_id: int
    duration_seconds: int | None = None
    is_active: bool


class NarrationSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    narration_id: int
    page_number: int
    audio_url: str
    duration_seconds: int | None = None


class NarrationGenerateRequest(BaseModel):
    book_id: int
    voice_key: str
    language: str
    replace_existing: bool = False


class NarrationGenerateResponse(BaseModel):
    narration: BookNarrationRead
    segments: list[NarrationSegmentRead]


class ReaderNarrationResponse(BaseModel):
    narration: BookNarrationRead
    segments: list[NarrationSegmentRead]
    voice: NarrationVoiceRead


class AvailableVoicesResponse(BaseModel):
    voices: list[NarrationVoiceRead]
