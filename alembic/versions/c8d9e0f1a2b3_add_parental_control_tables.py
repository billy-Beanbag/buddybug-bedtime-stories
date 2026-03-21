"""add parental control tables

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-03-13 22:20:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parentalcontrolsettings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bedtime_mode_default", sa.Boolean(), nullable=False),
        sa.Column("allow_audio_autoplay", sa.Boolean(), nullable=False),
        sa.Column("allow_8_12_content", sa.Boolean(), nullable=False),
        sa.Column("allow_premium_voice_content", sa.Boolean(), nullable=False),
        sa.Column("hide_adventure_content_at_bedtime", sa.Boolean(), nullable=False),
        sa.Column("max_allowed_age_band", sa.String(), nullable=False),
        sa.Column("quiet_mode_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    with op.batch_alter_table("parentalcontrolsettings", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_parentalcontrolsettings_user_id"), ["user_id"], unique=True)

    op.create_table(
        "childcontroloverride",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=False),
        sa.Column("bedtime_mode_enabled", sa.Boolean(), nullable=True),
        sa.Column("allow_audio_autoplay", sa.Boolean(), nullable=True),
        sa.Column("allow_8_12_content", sa.Boolean(), nullable=True),
        sa.Column("allow_premium_voice_content", sa.Boolean(), nullable=True),
        sa.Column("quiet_mode_enabled", sa.Boolean(), nullable=True),
        sa.Column("max_allowed_age_band", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("child_profile_id"),
    )
    with op.batch_alter_table("childcontroloverride", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_childcontroloverride_child_profile_id"), ["child_profile_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("childcontroloverride", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_childcontroloverride_child_profile_id"))
    op.drop_table("childcontroloverride")

    with op.batch_alter_table("parentalcontrolsettings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_parentalcontrolsettings_user_id"))
    op.drop_table("parentalcontrolsettings")
