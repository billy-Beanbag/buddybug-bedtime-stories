"""add notification tables

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-03-13 23:35:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "d9e0f1a2b3c4"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notificationpreference",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("enable_in_app", sa.Boolean(), nullable=False),
        sa.Column("enable_email_placeholder", sa.Boolean(), nullable=False),
        sa.Column("enable_bedtime_reminders", sa.Boolean(), nullable=False),
        sa.Column("enable_new_story_alerts", sa.Boolean(), nullable=False),
        sa.Column("enable_weekly_digest", sa.Boolean(), nullable=False),
        sa.Column("quiet_hours_start", sa.String(), nullable=True),
        sa.Column("quiet_hours_end", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    with op.batch_alter_table("notificationpreference", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_notificationpreference_user_id"), ["user_id"], unique=True)

    op.create_table(
        "notificationevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("notification_type", sa.String(), nullable=False),
        sa.Column("delivery_channel", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.String(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("delivered", sa.Boolean(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("notificationevent", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_notificationevent_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_notificationevent_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_notificationevent_notification_type"), ["notification_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_notificationevent_delivery_channel"), ["delivery_channel"], unique=False)

    op.create_table(
        "dailystorysuggestion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("suggestion_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "child_profile_id", "suggestion_date", name="uq_daily_story_user_child_date"),
    )
    with op.batch_alter_table("dailystorysuggestion", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_dailystorysuggestion_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_dailystorysuggestion_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_dailystorysuggestion_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_dailystorysuggestion_suggestion_date"), ["suggestion_date"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("dailystorysuggestion", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_dailystorysuggestion_suggestion_date"))
        batch_op.drop_index(batch_op.f("ix_dailystorysuggestion_book_id"))
        batch_op.drop_index(batch_op.f("ix_dailystorysuggestion_child_profile_id"))
        batch_op.drop_index(batch_op.f("ix_dailystorysuggestion_user_id"))
    op.drop_table("dailystorysuggestion")

    with op.batch_alter_table("notificationevent", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_notificationevent_delivery_channel"))
        batch_op.drop_index(batch_op.f("ix_notificationevent_notification_type"))
        batch_op.drop_index(batch_op.f("ix_notificationevent_child_profile_id"))
        batch_op.drop_index(batch_op.f("ix_notificationevent_user_id"))
    op.drop_table("notificationevent")

    with op.batch_alter_table("notificationpreference", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_notificationpreference_user_id"))
    op.drop_table("notificationpreference")
