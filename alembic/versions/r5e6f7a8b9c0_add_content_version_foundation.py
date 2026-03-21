"""add content version foundation

Revision ID: r5e6f7a8b9c0
Revises: q4d5e6f7a8b9
Create Date: 2026-03-16 10:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "r5e6f7a8b9c0"
down_revision = "q4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storydraftversion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("story_draft_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("full_text", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("review_status", sa.String(), nullable=False),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("approved_text", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["story_draft_id"], ["storydraft.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("storydraftversion", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_storydraftversion_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_storydraftversion_story_draft_id"), ["story_draft_id"], unique=False)

    op.create_table(
        "storypageversion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("story_page_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("page_text", sa.String(), nullable=False),
        sa.Column("scene_summary", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("mood", sa.String(), nullable=False),
        sa.Column("characters_present", sa.String(), nullable=False),
        sa.Column("illustration_prompt", sa.String(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["story_page_id"], ["storypage.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("storypageversion", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_storypageversion_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_storypageversion_story_page_id"), ["story_page_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("storypageversion", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storypageversion_story_page_id"))
        batch_op.drop_index(batch_op.f("ix_storypageversion_created_by_user_id"))

    op.drop_table("storypageversion")

    with op.batch_alter_table("storydraftversion", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storydraftversion_story_draft_id"))
        batch_op.drop_index(batch_op.f("ix_storydraftversion_created_by_user_id"))

    op.drop_table("storydraftversion")
