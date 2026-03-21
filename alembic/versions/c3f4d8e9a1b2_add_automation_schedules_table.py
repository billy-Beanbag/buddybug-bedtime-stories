"""add automation schedules table

Revision ID: c3f4d8e9a1b2
Revises: a6d9c4e1b2f0
Create Date: 2026-03-12 23:45:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = "c3f4d8e9a1b2"
down_revision = "a6d9c4e1b2f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "automationschedule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("schedule_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("cron_expression", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("interval_minutes", sa.Integer(), nullable=True),
        sa.Column("timezone", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("job_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("payload_json", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("policy_json", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_job_id", sa.Integer(), nullable=True),
        sa.Column("last_run_status", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["last_job_id"], ["workflowjob.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("automationschedule", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_automationschedule_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_automationschedule_job_type"), ["job_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_automationschedule_last_job_id"), ["last_job_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_automationschedule_name"), ["name"], unique=True)
        batch_op.create_index(batch_op.f("ix_automationschedule_schedule_type"), ["schedule_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("automationschedule", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_automationschedule_schedule_type"))
        batch_op.drop_index(batch_op.f("ix_automationschedule_name"))
        batch_op.drop_index(batch_op.f("ix_automationschedule_last_job_id"))
        batch_op.drop_index(batch_op.f("ix_automationschedule_job_type"))
        batch_op.drop_index(batch_op.f("ix_automationschedule_created_by_user_id"))

    op.drop_table("automationschedule")
