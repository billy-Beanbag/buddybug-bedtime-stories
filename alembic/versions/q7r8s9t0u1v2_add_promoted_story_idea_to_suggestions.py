"""add promoted story idea to suggestions

Revision ID: q7r8s9t0u1v2
Revises: c1d2e3f4a5b6
Create Date: 2026-04-02 16:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "q7r8s9t0u1v2"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("storysuggestion", sa.Column("promoted_story_idea_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_storysuggestion_promoted_story_idea_id"), "storysuggestion", ["promoted_story_idea_id"], unique=False)
    op.create_foreign_key(
        "fk_storysuggestion_promoted_story_idea_id_storyidea",
        "storysuggestion",
        "storyidea",
        ["promoted_story_idea_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_storysuggestion_promoted_story_idea_id_storyidea", "storysuggestion", type_="foreignkey")
    op.drop_index(op.f("ix_storysuggestion_promoted_story_idea_id"), table_name="storysuggestion")
    op.drop_column("storysuggestion", "promoted_story_idea_id")
