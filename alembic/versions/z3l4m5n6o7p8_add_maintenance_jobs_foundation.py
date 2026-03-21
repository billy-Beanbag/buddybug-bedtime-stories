"""add maintenance jobs foundation

Revision ID: z3l4m5n6o7p8
Revises: y2k3l4m5n6o7
Create Date: 2026-03-16 18:40:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "z3l4m5n6o7p8"
down_revision = "y2k3l4m5n6o7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenancejob",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("target_scope", sa.String(), nullable=True),
        sa.Column("parameters_json", sa.String(), nullable=True),
        sa.Column("result_json", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("maintenancejob", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_maintenancejob_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_maintenancejob_job_type"), ["job_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_maintenancejob_key"), ["key"], unique=False)
        batch_op.create_index(batch_op.f("ix_maintenancejob_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("maintenancejob", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_maintenancejob_status"))
        batch_op.drop_index(batch_op.f("ix_maintenancejob_key"))
        batch_op.drop_index(batch_op.f("ix_maintenancejob_job_type"))
        batch_op.drop_index(batch_op.f("ix_maintenancejob_created_by_user_id"))

    op.drop_table("maintenancejob")
