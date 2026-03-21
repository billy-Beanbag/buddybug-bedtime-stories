from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserEngagementStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    state_key: str
    last_active_at: datetime | None
    last_story_opened_at: datetime | None
    last_story_completed_at: datetime | None
    last_subscription_active_at: datetime | None
    active_child_profiles_count: int
    unread_saved_books_count: int
    unfinished_books_count: int
    preview_only_books_count: int
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


class ReengagementSuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    child_profile_id: int | None
    suggestion_type: str
    title: str
    body: str
    related_book_id: int | None
    state_key: str | None
    is_dismissed: bool
    created_at: datetime
    updated_at: datetime


class ReengagementSuggestionUpdate(BaseModel):
    is_dismissed: bool | None = None


class ReengagementDashboardResponse(BaseModel):
    engagement_state: UserEngagementStateRead | None
    suggestions: list[ReengagementSuggestionRead]
