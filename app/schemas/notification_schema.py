from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class NotificationPreferenceCreate(BaseModel):
    enable_in_app: bool = True
    enable_email_placeholder: bool = False
    enable_bedtime_reminders: bool = True
    enable_new_story_alerts: bool = True
    enable_weekly_digest: bool = False
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None


class NotificationPreferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    enable_in_app: bool
    enable_email_placeholder: bool
    enable_bedtime_reminders: bool
    enable_new_story_alerts: bool
    enable_weekly_digest: bool
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None
    created_at: datetime
    updated_at: datetime


class NotificationPreferenceUpdate(BaseModel):
    enable_in_app: bool | None = None
    enable_email_placeholder: bool | None = None
    enable_bedtime_reminders: bool | None = None
    enable_new_story_alerts: bool | None = None
    enable_weekly_digest: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None


class NotificationEventCreate(BaseModel):
    child_profile_id: int | None = None
    notification_type: str
    delivery_channel: str
    title: str
    body: str
    metadata_json: str | None = None
    scheduled_for: datetime | None = None


class NotificationEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    child_profile_id: int | None = None
    notification_type: str
    delivery_channel: str
    title: str
    body: str
    metadata_json: str | None = None
    is_read: bool
    delivered: bool
    scheduled_for: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class NotificationEventUpdate(BaseModel):
    is_read: bool | None = None
    delivered: bool | None = None


class DailyStorySuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    child_profile_id: int | None = None
    book_id: int
    suggestion_date: date
    reason: str | None = None
    created_at: datetime


class NotificationQueueResponse(BaseModel):
    items: list[NotificationEventRead]


class DailyStorySuggestionResponse(BaseModel):
    suggestion: DailyStorySuggestionRead | None
    book: dict[str, object] | None
