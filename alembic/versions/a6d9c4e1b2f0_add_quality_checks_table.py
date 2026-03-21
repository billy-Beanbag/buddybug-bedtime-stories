"""add quality checks table

Revision ID: a6d9c4e1b2f0
Revises: 7c1a5f4e2d3b
Create Date: 2026-03-12 23:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = "a6d9c4e1b2f0"
down_revision = "7c1a5f4e2d3b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "qualitycheck",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("target_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("check_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("issues_json", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("summary", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_by_job_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_job_id"], ["workflowjob.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("qualitycheck", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_qualitycheck_check_type"), ["check_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_qualitycheck_created_by_job_id"), ["created_by_job_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_qualitycheck_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_qualitycheck_target_id"), ["target_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_qualitycheck_target_type"), ["target_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("qualitycheck", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_qualitycheck_target_type"))
        batch_op.drop_index(batch_op.f("ix_qualitycheck_target_id"))
        batch_op.drop_index(batch_op.f("ix_qualitycheck_status"))
        batch_op.drop_index(batch_op.f("ix_qualitycheck_created_by_job_id"))
        batch_op.drop_index(batch_op.f("ix_qualitycheck_check_type"))

    op.drop_table("qualitycheck")
