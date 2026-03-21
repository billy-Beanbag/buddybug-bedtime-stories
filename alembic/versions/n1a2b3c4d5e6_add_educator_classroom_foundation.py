"""add educator classroom foundation

Revision ID: n1a2b3c4d5e6
Revises: m8n9o0p1q2r3
Create Date: 2026-03-15 18:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "n1a2b3c4d5e6"
down_revision = "m8n9o0p1q2r3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_educator", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "classroomset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("age_band", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("classroomset", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_classroomset_age_band"), ["age_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_classroomset_language"), ["language"], unique=False)
        batch_op.create_index(batch_op.f("ix_classroomset_user_id"), ["user_id"], unique=False)

    op.create_table(
        "classroomsetitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("classroom_set_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["classroom_set_id"], ["classroomset.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("classroom_set_id", "book_id", name="uq_classroom_set_book"),
    )
    with op.batch_alter_table("classroomsetitem", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_classroomsetitem_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_classroomsetitem_classroom_set_id"), ["classroom_set_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("classroomsetitem", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_classroomsetitem_classroom_set_id"))
        batch_op.drop_index(batch_op.f("ix_classroomsetitem_book_id"))

    op.drop_table("classroomsetitem")

    with op.batch_alter_table("classroomset", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_classroomset_user_id"))
        batch_op.drop_index(batch_op.f("ix_classroomset_language"))
        batch_op.drop_index(batch_op.f("ix_classroomset_age_band"))

    op.drop_table("classroomset")

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("is_educator")
