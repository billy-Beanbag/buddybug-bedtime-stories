from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReadAlongSessionCreate(BaseModel):
    book_id: int
    child_profile_id: int | None = None
    language: str | None = None
    current_page_number: int = 0
    playback_state: str = "paused"


class ReadAlongSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    child_profile_id: int | None = None
    book_id: int
    join_code: str
    status: str
    current_page_number: int
    playback_state: str
    language: str | None = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    ended_at: datetime | None = None


class ReadAlongParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    user_id: int
    child_profile_id: int | None = None
    role: str
    joined_at: datetime
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ReadAlongSessionUpdate(BaseModel):
    current_page_number: int | None = None
    playback_state: str | None = None
    status: str | None = None
    ended_at: datetime | None = None


class ReadAlongJoinRequest(BaseModel):
    join_code: str
    child_profile_id: int | None = None


class ReadAlongDetailResponse(BaseModel):
    session: ReadAlongSessionRead
    participants: list[ReadAlongParticipantRead]


class ReadAlongJoinResponse(BaseModel):
    session: ReadAlongSessionRead
    participant: ReadAlongParticipantRead
