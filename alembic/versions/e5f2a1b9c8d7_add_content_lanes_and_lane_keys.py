"""add content lanes and lane keys

Revision ID: e5f2a1b9c8d7
Revises: d4e7f1c2b3a4
Create Date: 2026-03-13 09:20:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision = "e5f2a1b9c8d7"
down_revision = "d4e7f1c2b3a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contentlane",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("age_band", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("tone_rules", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("writing_rules", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("illustration_rules", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("quality_rules", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("contentlane", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_contentlane_age_band"), ["age_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_contentlane_key"), ["key"], unique=True)

    with op.batch_alter_table("storyidea", schema=None) as batch_op:
        batch_op.add_column(sa.Column("content_lane_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.create_index(batch_op.f("ix_storyidea_content_lane_key"), ["content_lane_key"], unique=False)

    with op.batch_alter_table("storydraft", schema=None) as batch_op:
        batch_op.add_column(sa.Column("content_lane_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.create_index(batch_op.f("ix_storydraft_content_lane_key"), ["content_lane_key"], unique=False)

    with op.batch_alter_table("book", schema=None) as batch_op:
        batch_op.add_column(sa.Column("content_lane_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.create_index(batch_op.f("ix_book_content_lane_key"), ["content_lane_key"], unique=False)

    op.execute(
        sa.text(
            "UPDATE storyidea SET content_lane_key = CASE "
            "WHEN age_band = '8-12' THEN 'story_adventures_8_12' "
            "ELSE 'bedtime_3_7' END "
            "WHERE content_lane_key IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE storydraft SET content_lane_key = COALESCE(("
            "SELECT storyidea.content_lane_key FROM storyidea WHERE storyidea.id = storydraft.story_idea_id"
            "), 'bedtime_3_7') "
            "WHERE content_lane_key IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE book SET content_lane_key = COALESCE(("
            "SELECT storydraft.content_lane_key FROM storydraft WHERE storydraft.id = book.story_draft_id"
            "), 'bedtime_3_7') "
            "WHERE content_lane_key IS NULL"
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("book", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_book_content_lane_key"))
        batch_op.drop_column("content_lane_key")

    with op.batch_alter_table("storydraft", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storydraft_content_lane_key"))
        batch_op.drop_column("content_lane_key")

    with op.batch_alter_table("storyidea", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storyidea_content_lane_key"))
        batch_op.drop_column("content_lane_key")

    with op.batch_alter_table("contentlane", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_contentlane_key"))
        batch_op.drop_index(batch_op.f("ix_contentlane_age_band"))

    op.drop_table("contentlane")
