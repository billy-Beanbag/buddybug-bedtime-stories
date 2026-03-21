"""add changelog foundation

Revision ID: x1j2k3l4m5n6
Revises: v9i0j1k2l3m4
Create Date: 2026-03-16 14:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "x1j2k3l4m5n6"
down_revision = "v9i0j1k2l3m4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "changelogentry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version_label", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("details_markdown", sa.String(), nullable=True),
        sa.Column("audience", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("area_tags", sa.String(), nullable=True),
        sa.Column("feature_flag_keys", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("changelogentry", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_changelogentry_audience"), ["audience"], unique=False)
        batch_op.create_index(batch_op.f("ix_changelogentry_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_changelogentry_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_changelogentry_version_label"), ["version_label"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("changelogentry", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_changelogentry_version_label"))
        batch_op.drop_index(batch_op.f("ix_changelogentry_status"))
        batch_op.drop_index(batch_op.f("ix_changelogentry_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_changelogentry_audience"))

    op.drop_table("changelogentry")
