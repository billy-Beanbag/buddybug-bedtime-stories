"""add growth foundation

Revision ID: j5e6f7a8b9c0
Revises: i4d5e6f7a8b9
Create Date: 2026-03-13 19:15:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "j5e6f7a8b9c0"
down_revision = "i4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "referralcode",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("total_uses", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("referralcode", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_referralcode_code"), ["code"], unique=True)
        batch_op.create_index(batch_op.f("ix_referralcode_user_id"), ["user_id"], unique=True)

    op.create_table(
        "referralattribution",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("referrer_user_id", sa.Integer(), nullable=False),
        sa.Column("referred_user_id", sa.Integer(), nullable=False),
        sa.Column("referral_code_id", sa.Integer(), nullable=False),
        sa.Column("signup_attributed_at", sa.DateTime(), nullable=False),
        sa.Column("premium_converted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["referral_code_id"], ["referralcode.id"]),
        sa.ForeignKeyConstraint(["referred_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["referrer_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("referralattribution", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_referralattribution_referral_code_id"), ["referral_code_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_referralattribution_referred_user_id"), ["referred_user_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_referralattribution_referrer_user_id"), ["referrer_user_id"], unique=False)

    op.create_table(
        "giftsubscription",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchaser_user_id", sa.Integer(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("purchased_at", sa.DateTime(), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["purchaser_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("giftsubscription", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_giftsubscription_code"), ["code"], unique=True)
        batch_op.create_index(batch_op.f("ix_giftsubscription_purchaser_user_id"), ["purchaser_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_giftsubscription_recipient_user_id"), ["recipient_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_giftsubscription_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("giftsubscription", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_giftsubscription_status"))
        batch_op.drop_index(batch_op.f("ix_giftsubscription_recipient_user_id"))
        batch_op.drop_index(batch_op.f("ix_giftsubscription_purchaser_user_id"))
        batch_op.drop_index(batch_op.f("ix_giftsubscription_code"))
    op.drop_table("giftsubscription")

    with op.batch_alter_table("referralattribution", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_referralattribution_referrer_user_id"))
        batch_op.drop_index(batch_op.f("ix_referralattribution_referred_user_id"))
        batch_op.drop_index(batch_op.f("ix_referralattribution_referral_code_id"))
    op.drop_table("referralattribution")

    with op.batch_alter_table("referralcode", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_referralcode_user_id"))
        batch_op.drop_index(batch_op.f("ix_referralcode_code"))
    op.drop_table("referralcode")
