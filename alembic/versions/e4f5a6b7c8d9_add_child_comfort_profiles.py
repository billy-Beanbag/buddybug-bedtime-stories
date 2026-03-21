"""add child comfort profiles

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-03-20 09:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "childcomfortprofile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=False),
        sa.Column("favorite_characters_csv", sa.String(), nullable=True),
        sa.Column("favorite_moods_csv", sa.String(), nullable=True),
        sa.Column("favorite_story_types_csv", sa.String(), nullable=True),
        sa.Column("avoid_tags_csv", sa.String(), nullable=True),
        sa.Column("preferred_language", sa.String(), nullable=True),
        sa.Column("prefer_narration", sa.Boolean(), nullable=False),
        sa.Column("prefer_shorter_stories", sa.Boolean(), nullable=False),
        sa.Column("extra_calm_mode", sa.Boolean(), nullable=False),
        sa.Column("bedtime_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("childcomfortprofile", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_childcomfortprofile_child_profile_id"), ["child_profile_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("childcomfortprofile", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_childcomfortprofile_child_profile_id"))
    op.drop_table("childcomfortprofile")
