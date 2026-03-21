"""add api keys foundation

Revision ID: s6f7a8b9c0d1
Revises: r5e6f7a8b9c0
Create Date: 2026-03-16 11:15:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s6f7a8b9c0d1"
down_revision = "r5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apikey",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key_prefix", sa.String(), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("scopes", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("apikey", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_apikey_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_apikey_key_prefix"), ["key_prefix"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("apikey", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_apikey_key_prefix"))
        batch_op.drop_index(batch_op.f("ix_apikey_created_by_user_id"))

    op.drop_table("apikey")
