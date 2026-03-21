"""add visual references foundation

Revision ID: v9i0j1k2l3m4
Revises: u8h9i0j1k2l3
Create Date: 2026-03-16 13:20:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "v9i0j1k2l3m4"
down_revision = "u8h9i0j1k2l3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visualreferenceasset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("reference_type", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("prompt_notes", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("visualreferenceasset", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_visualreferenceasset_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_visualreferenceasset_reference_type"), ["reference_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_visualreferenceasset_target_id"), ["target_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_visualreferenceasset_target_type"), ["target_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("visualreferenceasset", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_visualreferenceasset_target_type"))
        batch_op.drop_index(batch_op.f("ix_visualreferenceasset_target_id"))
        batch_op.drop_index(batch_op.f("ix_visualreferenceasset_reference_type"))
        batch_op.drop_index(batch_op.f("ix_visualreferenceasset_created_by_user_id"))

    op.drop_table("visualreferenceasset")
