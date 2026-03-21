from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReferralAttribution(SQLModel, table=True):
    """Tracks which referred signup belongs to which referrer."""

    id: int | None = Field(default=None, primary_key=True)
    referrer_user_id: int = Field(foreign_key="user.id", index=True)
    referred_user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    referral_code_id: int = Field(foreign_key="referralcode.id", index=True)
    signup_attributed_at: datetime = Field(default_factory=utc_now, nullable=False)
    premium_converted_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
