from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class PromoAccessRedemption(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    promo_access_code_id: int = Field(foreign_key="promoaccesscode.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    redeemed_at: datetime = Field(default_factory=utc_now, nullable=False)
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
