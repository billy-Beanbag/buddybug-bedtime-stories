"""add workflow jobs table

Revision ID: 7c1a5f4e2d3b
Revises: 4f3f9d0d8f6c
Create Date: 2026-03-12 22:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = "7c1a5f4e2d3b"
down_revision = "4f3f9d0d8f6c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflowjob",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("payload_json", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("result_json", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("parent_job_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["parent_job_id"], ["workflowjob.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("workflowjob", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_workflowjob_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_workflowjob_job_type"), ["job_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_workflowjob_parent_job_id"), ["parent_job_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_workflowjob_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("workflowjob", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_workflowjob_status"))
        batch_op.drop_index(batch_op.f("ix_workflowjob_parent_job_id"))
        batch_op.drop_index(batch_op.f("ix_workflowjob_job_type"))
        batch_op.drop_index(batch_op.f("ix_workflowjob_created_by_user_id"))

    op.drop_table("workflowjob")
