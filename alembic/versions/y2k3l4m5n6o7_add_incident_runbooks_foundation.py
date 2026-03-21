"""add incident runbooks foundation

Revision ID: y2k3l4m5n6o7
Revises: x1j2k3l4m5n6
Create Date: 2026-03-16 16:20:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "y2k3l4m5n6o7"
down_revision = "x1j2k3l4m5n6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidentrecord",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("affected_area", sa.String(), nullable=False),
        sa.Column("feature_flag_key", sa.String(), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=True),
        sa.Column("mitigated_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("customer_impact_summary", sa.String(), nullable=True),
        sa.Column("root_cause_summary", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("incidentrecord", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_incidentrecord_affected_area"), ["affected_area"], unique=False)
        batch_op.create_index(batch_op.f("ix_incidentrecord_assigned_to_user_id"), ["assigned_to_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_incidentrecord_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_incidentrecord_severity"), ["severity"], unique=False)
        batch_op.create_index(batch_op.f("ix_incidentrecord_status"), ["status"], unique=False)

    op.create_table(
        "incidentupdate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=True),
        sa.Column("update_type", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["incident_id"], ["incidentrecord.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("incidentupdate", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_incidentupdate_author_user_id"), ["author_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_incidentupdate_incident_id"), ["incident_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_incidentupdate_update_type"), ["update_type"], unique=False)

    op.create_table(
        "runbookentry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("area", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("steps_markdown", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("runbookentry", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_runbookentry_area"), ["area"], unique=False)
        batch_op.create_index(batch_op.f("ix_runbookentry_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_runbookentry_key"), ["key"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("runbookentry", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_runbookentry_key"))
        batch_op.drop_index(batch_op.f("ix_runbookentry_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_runbookentry_area"))

    op.drop_table("runbookentry")

    with op.batch_alter_table("incidentupdate", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_incidentupdate_update_type"))
        batch_op.drop_index(batch_op.f("ix_incidentupdate_incident_id"))
        batch_op.drop_index(batch_op.f("ix_incidentupdate_author_user_id"))

    op.drop_table("incidentupdate")

    with op.batch_alter_table("incidentrecord", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_incidentrecord_status"))
        batch_op.drop_index(batch_op.f("ix_incidentrecord_severity"))
        batch_op.drop_index(batch_op.f("ix_incidentrecord_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_incidentrecord_assigned_to_user_id"))
        batch_op.drop_index(batch_op.f("ix_incidentrecord_affected_area"))

    op.drop_table("incidentrecord")
