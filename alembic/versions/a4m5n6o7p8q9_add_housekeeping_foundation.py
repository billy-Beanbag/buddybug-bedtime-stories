"""add housekeeping foundation

Revision ID: a4m5n6o7p8q9
Revises: z3l4m5n6o7p8
Create Date: 2026-03-16 21:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a4m5n6o7p8q9"
down_revision = "z3l4m5n6o7p8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "housekeepingpolicy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("target_table", sa.String(), nullable=False),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("dry_run_only", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("housekeepingpolicy", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_housekeepingpolicy_action_type"), ["action_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_housekeepingpolicy_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_housekeepingpolicy_key"), ["key"], unique=True)
        batch_op.create_index(batch_op.f("ix_housekeepingpolicy_target_table"), ["target_table"], unique=False)

    op.create_table(
        "housekeepingrun",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("affected_count", sa.Integer(), nullable=False),
        sa.Column("result_json", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["policy_id"], ["housekeepingpolicy.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("housekeepingrun", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_housekeepingrun_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_housekeepingrun_policy_id"), ["policy_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_housekeepingrun_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("housekeepingrun", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_housekeepingrun_status"))
        batch_op.drop_index(batch_op.f("ix_housekeepingrun_policy_id"))
        batch_op.drop_index(batch_op.f("ix_housekeepingrun_created_by_user_id"))

    op.drop_table("housekeepingrun")

    with op.batch_alter_table("housekeepingpolicy", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_housekeepingpolicy_target_table"))
        batch_op.drop_index(batch_op.f("ix_housekeepingpolicy_key"))
        batch_op.drop_index(batch_op.f("ix_housekeepingpolicy_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_housekeepingpolicy_action_type"))

    op.drop_table("housekeepingpolicy")
