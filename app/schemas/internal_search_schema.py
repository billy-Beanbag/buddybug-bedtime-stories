from pydantic import BaseModel


class InternalSearchResult(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    subtitle: str | None = None
    description: str | None = None
    route: str | None = None
    badge: str | None = None
    metadata_json: str | None = None


class InternalSearchGroup(BaseModel):
    entity_type: str
    label: str
    items: list[InternalSearchResult]


class InternalSearchResponse(BaseModel):
    query: str
    groups: list[InternalSearchGroup]


class QuickActionItem(BaseModel):
    key: str
    label: str
    route: str | None = None
    action_type: str
    entity_type: str | None = None
    entity_id: str | None = None
    description: str | None = None
    permission_hint: str | None = None


class QuickActionResponse(BaseModel):
    items: list[QuickActionItem]
