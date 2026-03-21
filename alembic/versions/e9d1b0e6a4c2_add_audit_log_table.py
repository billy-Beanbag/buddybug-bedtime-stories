"""add audit log table

Revision ID: e9d1b0e6a4c2
Revises: 8ec96ff2bfcf
Create Date: 2026-03-12 19:40:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = "e9d1b0e6a4c2"
down_revision = "8ec96ff2bfcf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auditlog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_email", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("action_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("entity_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("entity_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("summary", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("metadata_json", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("request_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("auditlog", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_auditlog_actor_user_id"), ["actor_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_auditlog_action_type"), ["action_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_auditlog_entity_type"), ["entity_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_auditlog_entity_id"), ["entity_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_auditlog_request_id"), ["request_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("auditlog", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_auditlog_request_id"))
        batch_op.drop_index(batch_op.f("ix_auditlog_entity_id"))
        batch_op.drop_index(batch_op.f("ix_auditlog_entity_type"))
        batch_op.drop_index(batch_op.f("ix_auditlog_action_type"))
        batch_op.drop_index(batch_op.f("ix_auditlog_actor_user_id"))

    op.drop_table("auditlog")
