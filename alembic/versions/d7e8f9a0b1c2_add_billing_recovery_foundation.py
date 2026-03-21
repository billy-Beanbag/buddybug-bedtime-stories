"""add billing recovery foundation

Revision ID: d7e8f9a0b1c2
Revises: c6p7q8r9s0t1
Create Date: 2026-03-17 14:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "d7e8f9a0b1c2"
down_revision = "c6p7q8r9s0t1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billingrecoverycase",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("external_reference", sa.String(), nullable=True),
        sa.Column("recovery_status", sa.String(), nullable=False),
        sa.Column("billing_status_snapshot", sa.String(), nullable=True),
        sa.Column("subscription_tier_snapshot", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("first_detected_at", sa.DateTime(), nullable=False),
        sa.Column("last_detected_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("billingrecoverycase", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_billingrecoverycase_external_reference"), ["external_reference"], unique=False)
        batch_op.create_index(batch_op.f("ix_billingrecoverycase_recovery_status"), ["recovery_status"], unique=False)
        batch_op.create_index(batch_op.f("ix_billingrecoverycase_source_type"), ["source_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_billingrecoverycase_user_id"), ["user_id"], unique=False)

    op.create_table(
        "billingrecoveryevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recovery_case_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["recovery_case_id"], ["billingrecoverycase.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("billingrecoveryevent", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_billingrecoveryevent_event_type"), ["event_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_billingrecoveryevent_recovery_case_id"), ["recovery_case_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("billingrecoveryevent", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_billingrecoveryevent_recovery_case_id"))
        batch_op.drop_index(batch_op.f("ix_billingrecoveryevent_event_type"))

    op.drop_table("billingrecoveryevent")

    with op.batch_alter_table("billingrecoverycase", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_billingrecoverycase_user_id"))
        batch_op.drop_index(batch_op.f("ix_billingrecoverycase_source_type"))
        batch_op.drop_index(batch_op.f("ix_billingrecoverycase_recovery_status"))
        batch_op.drop_index(batch_op.f("ix_billingrecoverycase_external_reference"))

    op.drop_table("billingrecoverycase")
