"""add moderation foundation

Revision ID: u8h9i0j1k2l3
Revises: t7g8h9i0j1k2
Create Date: 2026-03-16 12:40:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "u8h9i0j1k2l3"
down_revision = "t7g8h9i0j1k2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "moderationcase",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_type", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("moderationcase", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_moderationcase_assigned_to_user_id"), ["assigned_to_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_moderationcase_case_type"), ["case_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_moderationcase_severity"), ["severity"], unique=False)
        batch_op.create_index(batch_op.f("ix_moderationcase_source_id"), ["source_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_moderationcase_source_type"), ["source_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_moderationcase_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_moderationcase_target_id"), ["target_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_moderationcase_target_type"), ["target_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("moderationcase", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_moderationcase_target_type"))
        batch_op.drop_index(batch_op.f("ix_moderationcase_target_id"))
        batch_op.drop_index(batch_op.f("ix_moderationcase_status"))
        batch_op.drop_index(batch_op.f("ix_moderationcase_source_type"))
        batch_op.drop_index(batch_op.f("ix_moderationcase_source_id"))
        batch_op.drop_index(batch_op.f("ix_moderationcase_severity"))
        batch_op.drop_index(batch_op.f("ix_moderationcase_case_type"))
        batch_op.drop_index(batch_op.f("ix_moderationcase_assigned_to_user_id"))

    op.drop_table("moderationcase")
