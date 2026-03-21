"""add library download tables

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-03-13 13:25:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision = "a1b2c3d4e5f6"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "userlibraryitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("saved_for_offline", sa.Boolean(), nullable=False),
        sa.Column("last_opened_at", sa.DateTime(), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("userlibraryitem", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_userlibraryitem_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_userlibraryitem_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_userlibraryitem_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_userlibraryitem_status"), ["status"], unique=False)

    op.create_table(
        "bookdownloadpackage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("language", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("package_version", sa.Integer(), nullable=False),
        sa.Column("package_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("package_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("bookdownloadpackage", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_bookdownloadpackage_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookdownloadpackage_language"), ["language"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("bookdownloadpackage", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bookdownloadpackage_language"))
        batch_op.drop_index(batch_op.f("ix_bookdownloadpackage_book_id"))
    op.drop_table("bookdownloadpackage")

    with op.batch_alter_table("userlibraryitem", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_userlibraryitem_status"))
        batch_op.drop_index(batch_op.f("ix_userlibraryitem_book_id"))
        batch_op.drop_index(batch_op.f("ix_userlibraryitem_child_profile_id"))
        batch_op.drop_index(batch_op.f("ix_userlibraryitem_user_id"))
    op.drop_table("userlibraryitem")
