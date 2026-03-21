"""add story brief foundation

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-03-17 13:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a9b0c1d2e3f4"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storybrief",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("story_idea_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("hook_type", sa.String(), nullable=False),
        sa.Column("target_age_band", sa.String(), nullable=False),
        sa.Column("tone", sa.String(), nullable=False),
        sa.Column("brief_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["story_idea_id"], ["storyidea.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("storybrief", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_storybrief_story_idea_id"), ["story_idea_id"], unique=True)

    with op.batch_alter_table("storyreviewqueue", schema=None) as batch_op:
        batch_op.add_column(sa.Column("story_brief", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("storyreviewqueue", schema=None) as batch_op:
        batch_op.drop_column("story_brief")

    with op.batch_alter_table("storybrief", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storybrief_story_idea_id"))
    op.drop_table("storybrief")
