"""add seasonal campaigns foundation

Revision ID: m8n9o0p1q2r3
Revises: l7g8h9i0j1k2
Create Date: 2026-03-15 14:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "m8n9o0p1q2r3"
down_revision = "l7g8h9i0j1k2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seasonalcampaign",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("age_band", sa.String(), nullable=True),
        sa.Column("content_lane_key", sa.String(), nullable=True),
        sa.Column("homepage_badge_text", sa.String(), nullable=True),
        sa.Column("homepage_cta_label", sa.String(), nullable=True),
        sa.Column("homepage_cta_route", sa.String(), nullable=True),
        sa.Column("banner_style_key", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("seasonalcampaign", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_seasonalcampaign_age_band"), ["age_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_seasonalcampaign_content_lane_key"), ["content_lane_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_seasonalcampaign_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_seasonalcampaign_key"), ["key"], unique=True)
        batch_op.create_index(batch_op.f("ix_seasonalcampaign_language"), ["language"], unique=False)

    op.create_table(
        "seasonalcampaignitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["campaign_id"], ["seasonalcampaign.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "book_id", name="uq_seasonal_campaign_book"),
    )
    with op.batch_alter_table("seasonalcampaignitem", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_seasonalcampaignitem_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_seasonalcampaignitem_campaign_id"), ["campaign_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("seasonalcampaignitem", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_seasonalcampaignitem_campaign_id"))
        batch_op.drop_index(batch_op.f("ix_seasonalcampaignitem_book_id"))

    op.drop_table("seasonalcampaignitem")

    with op.batch_alter_table("seasonalcampaign", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_seasonalcampaign_language"))
        batch_op.drop_index(batch_op.f("ix_seasonalcampaign_key"))
        batch_op.drop_index(batch_op.f("ix_seasonalcampaign_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_seasonalcampaign_content_lane_key"))
        batch_op.drop_index(batch_op.f("ix_seasonalcampaign_age_band"))

    op.drop_table("seasonalcampaign")
