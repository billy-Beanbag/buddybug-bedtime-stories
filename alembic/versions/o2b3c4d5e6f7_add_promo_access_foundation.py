"""add promo access foundation

Revision ID: o2b3c4d5e6f7
Revises: n1a2b3c4d5e6
Create Date: 2026-03-15 20:15:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "o2b3c4d5e6f7"
down_revision = "n1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "promoaccesscode",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("partner_name", sa.String(), nullable=True),
        sa.Column("access_type", sa.String(), nullable=False),
        sa.Column("subscription_tier_granted", sa.String(), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("redemption_count", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("promoaccesscode", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_promoaccesscode_access_type"), ["access_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_promoaccesscode_code"), ["code"], unique=True)
        batch_op.create_index(batch_op.f("ix_promoaccesscode_key"), ["key"], unique=True)

    op.create_table(
        "promoaccessredemption",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("promo_access_code_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["promo_access_code_id"], ["promoaccesscode.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("promoaccessredemption", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_promoaccessredemption_promo_access_code_id"), ["promo_access_code_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_promoaccessredemption_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("promoaccessredemption", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_promoaccessredemption_user_id"))
        batch_op.drop_index(batch_op.f("ix_promoaccessredemption_promo_access_code_id"))

    op.drop_table("promoaccessredemption")

    with op.batch_alter_table("promoaccesscode", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_promoaccesscode_key"))
        batch_op.drop_index(batch_op.f("ix_promoaccesscode_code"))
        batch_op.drop_index(batch_op.f("ix_promoaccesscode_access_type"))

    op.drop_table("promoaccesscode")
