from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VisualReferenceAssetCreate(BaseModel):
    name: str
    reference_type: str
    target_type: str | None = None
    target_id: int | None = None
    image_url: str
    prompt_notes: str | None = None
    language: str | None = None
    is_active: bool = True


class VisualReferenceAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    reference_type: str
    target_type: str | None = None
    target_id: int | None = None
    image_url: str
    prompt_notes: str | None = None
    language: str | None = None
    is_active: bool
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class VisualReferenceAssetUpdate(BaseModel):
    name: str | None = None
    reference_type: str | None = None
    target_type: str | None = None
    target_id: int | None = None
    image_url: str | None = None
    prompt_notes: str | None = None
    language: str | None = None
    is_active: bool | None = None


class VisualReferenceImportResponse(BaseModel):
    created: int
    updated: int
    scanned: int
    created_tables: bool = False
