"""add reading plans foundation

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-19 13:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "readingplan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("plan_type", sa.String(), nullable=False),
        sa.Column("preferred_age_band", sa.String(), nullable=True),
        sa.Column("preferred_language", sa.String(), nullable=True),
        sa.Column("preferred_content_lane_key", sa.String(), nullable=True),
        sa.Column("prefer_narration", sa.Boolean(), nullable=False),
        sa.Column("sessions_per_week", sa.Integer(), nullable=False),
        sa.Column("target_days_csv", sa.String(), nullable=True),
        sa.Column("bedtime_mode_preferred", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("readingplan", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_readingplan_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_readingplan_plan_type"), ["plan_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_readingplan_preferred_age_band"), ["preferred_age_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_readingplan_preferred_content_lane_key"), ["preferred_content_lane_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_readingplan_preferred_language"), ["preferred_language"], unique=False)
        batch_op.create_index(batch_op.f("ix_readingplan_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_readingplan_user_id"), ["user_id"], unique=False)

    op.create_table(
        "readingplansession",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reading_plan_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("suggested_book_id", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["reading_plan_id"], ["readingplan.id"]),
        sa.ForeignKeyConstraint(["suggested_book_id"], ["book.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reading_plan_id", "scheduled_date", name="uq_reading_plan_session_plan_date"),
    )
    with op.batch_alter_table("readingplansession", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_readingplansession_reading_plan_id"), ["reading_plan_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_readingplansession_scheduled_date"), ["scheduled_date"], unique=False)
        batch_op.create_index(batch_op.f("ix_readingplansession_suggested_book_id"), ["suggested_book_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("readingplansession", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_readingplansession_suggested_book_id"))
        batch_op.drop_index(batch_op.f("ix_readingplansession_scheduled_date"))
        batch_op.drop_index(batch_op.f("ix_readingplansession_reading_plan_id"))
    op.drop_table("readingplansession")

    with op.batch_alter_table("readingplan", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_readingplan_user_id"))
        batch_op.drop_index(batch_op.f("ix_readingplan_status"))
        batch_op.drop_index(batch_op.f("ix_readingplan_preferred_language"))
        batch_op.drop_index(batch_op.f("ix_readingplan_preferred_content_lane_key"))
        batch_op.drop_index(batch_op.f("ix_readingplan_preferred_age_band"))
        batch_op.drop_index(batch_op.f("ix_readingplan_plan_type"))
        batch_op.drop_index(batch_op.f("ix_readingplan_child_profile_id"))
    op.drop_table("readingplan")
