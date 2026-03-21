"""add story quality reviews

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-03-20 13:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storyqualityreview",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("story_id", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("flagged_issues_json", sa.String(), nullable=False),
        sa.Column("evaluation_summary", sa.String(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["storydraft.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("storyqualityreview", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_storyqualityreview_story_id"), ["story_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_storyqualityreview_review_required"), ["review_required"], unique=False)

    op.create_table(
        "illustrationqualityreview",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("illustration_id", sa.Integer(), nullable=False),
        sa.Column("story_id", sa.Integer(), nullable=True),
        sa.Column("style_consistency_score", sa.Integer(), nullable=False),
        sa.Column("character_consistency_score", sa.Integer(), nullable=False),
        sa.Column("color_palette_score", sa.Integer(), nullable=False),
        sa.Column("flagged_issues_json", sa.String(), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["illustration_id"], ["illustration.id"]),
        sa.ForeignKeyConstraint(["story_id"], ["storydraft.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("illustrationqualityreview", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_illustrationqualityreview_illustration_id"), ["illustration_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_illustrationqualityreview_story_id"), ["story_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_illustrationqualityreview_review_required"), ["review_required"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("illustrationqualityreview", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_illustrationqualityreview_review_required"))
        batch_op.drop_index(batch_op.f("ix_illustrationqualityreview_story_id"))
        batch_op.drop_index(batch_op.f("ix_illustrationqualityreview_illustration_id"))
    op.drop_table("illustrationqualityreview")

    with op.batch_alter_table("storyqualityreview", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storyqualityreview_review_required"))
        batch_op.drop_index(batch_op.f("ix_storyqualityreview_story_id"))
    op.drop_table("storyqualityreview")
