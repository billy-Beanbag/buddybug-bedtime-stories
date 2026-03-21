"""add translation ops foundation

Revision ID: t7g8h9i0j1k2
Revises: s6f7a8b9c0d1
Create Date: 2026-03-16 12:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "t7g8h9i0j1k2"
down_revision = "s6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "translationtask",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("source_version_label", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "language", name="uq_translation_task_book_language"),
    )
    with op.batch_alter_table("translationtask", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_translationtask_assigned_to_user_id"), ["assigned_to_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_translationtask_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_translationtask_language"), ["language"], unique=False)
        batch_op.create_index(batch_op.f("ix_translationtask_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("translationtask", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_translationtask_status"))
        batch_op.drop_index(batch_op.f("ix_translationtask_language"))
        batch_op.drop_index(batch_op.f("ix_translationtask_book_id"))
        batch_op.drop_index(batch_op.f("ix_translationtask_assigned_to_user_id"))

    op.drop_table("translationtask")
