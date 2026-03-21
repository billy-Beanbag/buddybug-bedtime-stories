"""add narrated story tables

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-13 18:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision = "b7c8d9e0f1a2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("narrationvoice", schema=None) as batch_op:
        batch_op.add_column(sa.Column("gender", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column("style", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "booknarration",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("language", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("narration_voice_id", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["narration_voice_id"], ["narrationvoice.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("booknarration", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_booknarration_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_booknarration_language"), ["language"], unique=False)
        batch_op.create_index(batch_op.f("ix_booknarration_narration_voice_id"), ["narration_voice_id"], unique=False)

    op.create_table(
        "narrationsegment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("narration_id", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("audio_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["narration_id"], ["booknarration.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("narration_id", "page_number", name="uq_narrationsegment_narration_page"),
    )
    with op.batch_alter_table("narrationsegment", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_narrationsegment_narration_id"), ["narration_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_narrationsegment_page_number"), ["page_number"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("narrationsegment", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_narrationsegment_page_number"))
        batch_op.drop_index(batch_op.f("ix_narrationsegment_narration_id"))
    op.drop_table("narrationsegment")

    with op.batch_alter_table("booknarration", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_booknarration_narration_voice_id"))
        batch_op.drop_index(batch_op.f("ix_booknarration_language"))
        batch_op.drop_index(batch_op.f("ix_booknarration_book_id"))
    op.drop_table("booknarration")

    with op.batch_alter_table("narrationvoice", schema=None) as batch_op:
        batch_op.drop_column("is_premium")
        batch_op.drop_column("style")
        batch_op.drop_column("gender")
