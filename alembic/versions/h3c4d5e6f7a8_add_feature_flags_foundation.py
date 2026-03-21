"""add feature flags foundation

Revision ID: h3c4d5e6f7a8
Revises: g2b3c4d5e6f7
Create Date: 2026-03-13 17:20:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "h3c4d5e6f7a8"
down_revision = "g2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "featureflag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False),
        sa.Column("environments", sa.String(), nullable=True),
        sa.Column("target_subscription_tiers", sa.String(), nullable=True),
        sa.Column("target_languages", sa.String(), nullable=True),
        sa.Column("target_age_bands", sa.String(), nullable=True),
        sa.Column("target_roles", sa.String(), nullable=True),
        sa.Column("target_user_ids", sa.String(), nullable=True),
        sa.Column("target_countries", sa.String(), nullable=True),
        sa.Column("is_internal_only", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("rollout_percentage >= 0 AND rollout_percentage <= 100", name="ck_featureflag_rollout_percentage"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("featureflag", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_featureflag_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_featureflag_key"), ["key"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("featureflag", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_featureflag_key"))
        batch_op.drop_index(batch_op.f("ix_featureflag_created_by_user_id"))
    op.drop_table("featureflag")
