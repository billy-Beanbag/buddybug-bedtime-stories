"""add lifecycle timeline foundation

Revision ID: e1f2a3b4c5d6
Revises: d7e8f9a0b1c2
Create Date: 2026-03-18 10:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "e1f2a3b4c5d6"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lifecyclemilestone",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("milestone_type", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("source_table", sa.String(), nullable=True),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("lifecyclemilestone", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_lifecyclemilestone_milestone_type"), ["milestone_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_lifecyclemilestone_occurred_at"), ["occurred_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_lifecyclemilestone_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("lifecyclemilestone", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_lifecyclemilestone_user_id"))
        batch_op.drop_index(batch_op.f("ix_lifecyclemilestone_occurred_at"))
        batch_op.drop_index(batch_op.f("ix_lifecyclemilestone_milestone_type"))

    op.drop_table("lifecyclemilestone")
