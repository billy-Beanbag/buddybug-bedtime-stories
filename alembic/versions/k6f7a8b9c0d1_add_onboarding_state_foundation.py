"""add onboarding state foundation

Revision ID: k6f7a8b9c0d1
Revises: j5e6f7a8b9c0
Create Date: 2026-03-14 09:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "k6f7a8b9c0d1"
down_revision = "j5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "onboardingstate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.String(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("skipped", sa.Boolean(), nullable=False),
        sa.Column("child_profile_created", sa.Boolean(), nullable=False),
        sa.Column("preferred_age_band", sa.String(), nullable=True),
        sa.Column("preferred_language", sa.String(), nullable=True),
        sa.Column("bedtime_mode_reviewed", sa.Boolean(), nullable=False),
        sa.Column("first_story_opened", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("onboardingstate", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_onboardingstate_user_id"), ["user_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("onboardingstate", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_onboardingstate_user_id"))

    op.drop_table("onboardingstate")
