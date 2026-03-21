"""add story pipeline tables

Revision ID: f8a9b0c1d2e3
Revises: f5a6b7c8d9e0
Create Date: 2026-03-16 23:40:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f8a9b0c1d2e3"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("storyidea", schema=None) as batch_op:
        batch_op.add_column(sa.Column("hook_type", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("series_key", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("series_title", sa.String(), nullable=True))
        batch_op.create_index(batch_op.f("ix_storyidea_hook_type"), ["hook_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_storyidea_series_key"), ["series_key"], unique=False)

    op.create_table(
        "storystyletrainingdata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_story", sa.String(), nullable=False),
        sa.Column("edited_story", sa.String(), nullable=False),
        sa.Column("edit_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "storyreviewqueue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("story_id", sa.Integer(), nullable=False),
        sa.Column("generated_story", sa.String(), nullable=False),
        sa.Column("rewritten_story", sa.String(), nullable=False),
        sa.Column("outline", sa.String(), nullable=False),
        sa.Column("illustration_plan", sa.String(), nullable=False),
        sa.Column("story_metadata", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["storydraft.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("storyreviewqueue", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_storyreviewqueue_story_id"), ["story_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_storyreviewqueue_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("storyreviewqueue", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storyreviewqueue_status"))
        batch_op.drop_index(batch_op.f("ix_storyreviewqueue_story_id"))
    op.drop_table("storyreviewqueue")

    op.drop_table("storystyletrainingdata")

    with op.batch_alter_table("storyidea", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storyidea_series_key"))
        batch_op.drop_index(batch_op.f("ix_storyidea_hook_type"))
        batch_op.drop_column("series_title")
        batch_op.drop_column("series_key")
        batch_op.drop_column("hook_type")
