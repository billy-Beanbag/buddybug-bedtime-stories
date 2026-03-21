"""add public status foundation

Revision ID: c6p7q8r9s0t1
Revises: b5n6o7p8q9r0
Create Date: 2026-03-17 10:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c6p7q8r9s0t1"
down_revision = "b5n6o7p8q9r0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "publicstatuscomponent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("current_status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("publicstatuscomponent", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_publicstatuscomponent_current_status"), ["current_status"], unique=False)
        batch_op.create_index(batch_op.f("ix_publicstatuscomponent_key"), ["key"], unique=True)

    op.create_table(
        "publicstatusnotice",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("notice_type", sa.String(), nullable=False),
        sa.Column("public_status", sa.String(), nullable=False),
        sa.Column("component_key", sa.String(), nullable=True),
        sa.Column("linked_incident_id", sa.Integer(), nullable=True),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["linked_incident_id"], ["incidentrecord.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("publicstatusnotice", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_publicstatusnotice_component_key"), ["component_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_publicstatusnotice_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_publicstatusnotice_linked_incident_id"), ["linked_incident_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_publicstatusnotice_notice_type"), ["notice_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_publicstatusnotice_public_status"), ["public_status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("publicstatusnotice", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_publicstatusnotice_public_status"))
        batch_op.drop_index(batch_op.f("ix_publicstatusnotice_notice_type"))
        batch_op.drop_index(batch_op.f("ix_publicstatusnotice_linked_incident_id"))
        batch_op.drop_index(batch_op.f("ix_publicstatusnotice_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_publicstatusnotice_component_key"))

    op.drop_table("publicstatusnotice")

    with op.batch_alter_table("publicstatuscomponent", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_publicstatuscomponent_key"))
        batch_op.drop_index(batch_op.f("ix_publicstatuscomponent_current_status"))

    op.drop_table("publicstatuscomponent")
