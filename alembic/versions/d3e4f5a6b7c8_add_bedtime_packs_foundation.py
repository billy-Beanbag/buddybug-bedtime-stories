"""add bedtime packs foundation

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-03-19 18:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bedtimepack",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("pack_type", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("age_band", sa.String(), nullable=True),
        sa.Column("content_lane_key", sa.String(), nullable=True),
        sa.Column("prefer_narration", sa.Boolean(), nullable=False),
        sa.Column("generated_reason", sa.String(), nullable=True),
        sa.Column("active_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("bedtimepack", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_bedtimepack_active_date"), ["active_date"], unique=False)
        batch_op.create_index(batch_op.f("ix_bedtimepack_age_band"), ["age_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_bedtimepack_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_bedtimepack_content_lane_key"), ["content_lane_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_bedtimepack_language"), ["language"], unique=False)
        batch_op.create_index(batch_op.f("ix_bedtimepack_pack_type"), ["pack_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_bedtimepack_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_bedtimepack_user_id"), ["user_id"], unique=False)

    op.create_table(
        "bedtimepackitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bedtime_pack_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("recommended_narration", sa.Boolean(), nullable=False),
        sa.Column("completion_status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bedtime_pack_id"], ["bedtimepack.id"]),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bedtime_pack_id", "book_id", name="uq_bedtime_pack_item_pack_book"),
    )
    with op.batch_alter_table("bedtimepackitem", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_bedtimepackitem_bedtime_pack_id"), ["bedtime_pack_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_bedtimepackitem_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_bedtimepackitem_completion_status"), ["completion_status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("bedtimepackitem", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bedtimepackitem_completion_status"))
        batch_op.drop_index(batch_op.f("ix_bedtimepackitem_book_id"))
        batch_op.drop_index(batch_op.f("ix_bedtimepackitem_bedtime_pack_id"))
    op.drop_table("bedtimepackitem")

    with op.batch_alter_table("bedtimepack", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bedtimepack_user_id"))
        batch_op.drop_index(batch_op.f("ix_bedtimepack_status"))
        batch_op.drop_index(batch_op.f("ix_bedtimepack_pack_type"))
        batch_op.drop_index(batch_op.f("ix_bedtimepack_language"))
        batch_op.drop_index(batch_op.f("ix_bedtimepack_content_lane_key"))
        batch_op.drop_index(batch_op.f("ix_bedtimepack_child_profile_id"))
        batch_op.drop_index(batch_op.f("ix_bedtimepack_age_band"))
        batch_op.drop_index(batch_op.f("ix_bedtimepack_active_date"))
    op.drop_table("bedtimepack")
