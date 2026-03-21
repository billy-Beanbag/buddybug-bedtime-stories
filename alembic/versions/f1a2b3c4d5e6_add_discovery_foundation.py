"""add discovery foundation

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-03-13 13:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bookdiscoverymetadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("searchable_title", sa.String(), nullable=False),
        sa.Column("searchable_summary", sa.String(), nullable=True),
        sa.Column("searchable_text", sa.String(), nullable=True),
        sa.Column("age_band", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("content_lane_key", sa.String(), nullable=True),
        sa.Column("tone_tags", sa.String(), nullable=True),
        sa.Column("theme_tags", sa.String(), nullable=True),
        sa.Column("character_tags", sa.String(), nullable=True),
        sa.Column("setting_tags", sa.String(), nullable=True),
        sa.Column("style_tags", sa.String(), nullable=True),
        sa.Column("bedtime_safe", sa.Boolean(), nullable=False),
        sa.Column("adventure_level", sa.String(), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id"),
    )
    with op.batch_alter_table("bookdiscoverymetadata", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_bookdiscoverymetadata_book_id"), ["book_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_bookdiscoverymetadata_searchable_title"), ["searchable_title"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookdiscoverymetadata_age_band"), ["age_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookdiscoverymetadata_language"), ["language"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookdiscoverymetadata_content_lane_key"), ["content_lane_key"], unique=False)

    op.create_table(
        "bookcollection",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("age_band", sa.String(), nullable=True),
        sa.Column("content_lane_key", sa.String(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("is_featured", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    with op.batch_alter_table("bookcollection", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_bookcollection_key"), ["key"], unique=True)
        batch_op.create_index(batch_op.f("ix_bookcollection_language"), ["language"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookcollection_age_band"), ["age_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookcollection_content_lane_key"), ["content_lane_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookcollection_created_by_user_id"), ["created_by_user_id"], unique=False)

    op.create_table(
        "bookcollectionitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["collection_id"], ["bookcollection.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("collection_id", "book_id", name="uq_book_collection_item_collection_book"),
    )
    with op.batch_alter_table("bookcollectionitem", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_bookcollectionitem_collection_id"), ["collection_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookcollectionitem_book_id"), ["book_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("bookcollectionitem", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bookcollectionitem_book_id"))
        batch_op.drop_index(batch_op.f("ix_bookcollectionitem_collection_id"))
    op.drop_table("bookcollectionitem")

    with op.batch_alter_table("bookcollection", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bookcollection_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_bookcollection_content_lane_key"))
        batch_op.drop_index(batch_op.f("ix_bookcollection_age_band"))
        batch_op.drop_index(batch_op.f("ix_bookcollection_language"))
        batch_op.drop_index(batch_op.f("ix_bookcollection_key"))
    op.drop_table("bookcollection")

    with op.batch_alter_table("bookdiscoverymetadata", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bookdiscoverymetadata_content_lane_key"))
        batch_op.drop_index(batch_op.f("ix_bookdiscoverymetadata_language"))
        batch_op.drop_index(batch_op.f("ix_bookdiscoverymetadata_age_band"))
        batch_op.drop_index(batch_op.f("ix_bookdiscoverymetadata_searchable_title"))
        batch_op.drop_index(batch_op.f("ix_bookdiscoverymetadata_book_id"))
    op.drop_table("bookdiscoverymetadata")
