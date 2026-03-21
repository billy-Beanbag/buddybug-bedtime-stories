from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class CharacterBase(SQLModel):
    name: str
    role: str
    species: str
    short_description: str
    visual_description: str
    personality_traits: str
    style_rules: str
    color_palette: str | None = None
    accessories: str | None = None
    age_group: str | None = None
    is_active: bool = True


class CharacterCreate(CharacterBase):
    pass


class CharacterRead(CharacterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class CharacterUpdate(SQLModel):
    name: str | None = None
    role: str | None = None
    species: str | None = None
    short_description: str | None = None
    visual_description: str | None = None
    personality_traits: str | None = None
    style_rules: str | None = None
    color_palette: str | None = None
    accessories: str | None = None
    age_group: str | None = None
    is_active: bool | None = None
