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
    is_active: bool = True


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


class NarrationGenerateDefaultRequest(BaseModel):
    book_id: int
    language: str
    replace_existing: bool = False


class NarrationGenerateResponse(BaseModel):
    narration: BookNarrationRead
    segments: list[NarrationSegmentRead]


class NarrationBackfillRequest(BaseModel):
    book_ids: list[int] | None = None
    replace_existing: bool = False


class NarrationBackfillItem(BaseModel):
    book_id: int
    voice_key: str
    language: str
    narration_id: int


class NarrationBackfillResponse(BaseModel):
    items: list[NarrationBackfillItem]


class ChildNameNarrationGenerateRequest(BaseModel):
    child_profile_id: int
    voice_key: str
    language: str
    source_text: str | None = None
    snippet_type: str = "name_only"
    replace_existing: bool = False


class ChildNameNarrationAssetRead(BaseModel):
    child_profile_id: int
    voice_key: str
    language: str
    source_text: str
    snippet_type: str
    audio_url: str
    duration_seconds: int | None = None
    provider: str
    cached: bool


class ReaderNarrationResponse(BaseModel):
    narration: BookNarrationRead
    segments: list[NarrationSegmentRead]
    voice: NarrationVoiceRead


class AvailableVoicesResponse(BaseModel):
    voices: list[NarrationVoiceRead]
