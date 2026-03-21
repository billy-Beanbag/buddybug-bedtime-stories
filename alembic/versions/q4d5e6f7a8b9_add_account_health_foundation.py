"""add account health foundation

Revision ID: q4d5e6f7a8b9
Revises: p3c4d5e6f7a8
Create Date: 2026-03-15 23:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "q4d5e6f7a8b9"
down_revision = "p3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounthealthsnapshot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("health_score", sa.Integer(), nullable=False),
        sa.Column("health_band", sa.String(), nullable=False),
        sa.Column("active_children_count", sa.Integer(), nullable=False),
        sa.Column("stories_opened_30d", sa.Integer(), nullable=False),
        sa.Column("stories_completed_30d", sa.Integer(), nullable=False),
        sa.Column("saved_books_count", sa.Integer(), nullable=False),
        sa.Column("support_tickets_open_count", sa.Integer(), nullable=False),
        sa.Column("premium_status", sa.String(), nullable=True),
        sa.Column("dormant_days", sa.Integer(), nullable=True),
        sa.Column("snapshot_reasoning", sa.String(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("accounthealthsnapshot", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_accounthealthsnapshot_health_band"), ["health_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_accounthealthsnapshot_premium_status"), ["premium_status"], unique=False)
        batch_op.create_index(batch_op.f("ix_accounthealthsnapshot_user_id"), ["user_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("accounthealthsnapshot", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_accounthealthsnapshot_user_id"))
        batch_op.drop_index(batch_op.f("ix_accounthealthsnapshot_premium_status"))
        batch_op.drop_index(batch_op.f("ix_accounthealthsnapshot_health_band"))

    op.drop_table("accounthealthsnapshot")
