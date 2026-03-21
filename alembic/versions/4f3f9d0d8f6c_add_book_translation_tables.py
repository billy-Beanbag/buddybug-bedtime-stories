"""add book translation tables

Revision ID: 4f3f9d0d8f6c
Revises: e9d1b0e6a4c2
Create Date: 2026-03-12 20:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = "4f3f9d0d8f6c"
down_revision = "e9d1b0e6a4c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "booktranslation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("language", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "language", name="uq_book_translation_book_language"),
    )
    with op.batch_alter_table("booktranslation", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_booktranslation_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_booktranslation_language"), ["language"], unique=False)

    op.create_table(
        "bookpagetranslation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_page_id", sa.Integer(), nullable=False),
        sa.Column("language", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("text_content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_page_id"], ["bookpage.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_page_id", "language", name="uq_book_page_translation_page_language"),
    )
    with op.batch_alter_table("bookpagetranslation", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_bookpagetranslation_book_page_id"), ["book_page_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookpagetranslation_language"), ["language"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("bookpagetranslation", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bookpagetranslation_language"))
        batch_op.drop_index(batch_op.f("ix_bookpagetranslation_book_page_id"))

    op.drop_table("bookpagetranslation")

    with op.batch_alter_table("booktranslation", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_booktranslation_language"))
        batch_op.drop_index(batch_op.f("ix_booktranslation_book_id"))

    op.drop_table("booktranslation")
