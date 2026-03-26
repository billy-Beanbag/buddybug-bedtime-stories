"""add story suggestions foundation

Revision ID: c1d2e3f4a5b6
Revises: b0c1d2e3f4a5
Create Date: 2026-03-26 10:40:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c1d2e3f4a5b6"
down_revision = "b0c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storysuggestion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("brief", sa.String(), nullable=False),
        sa.Column("desired_outcome", sa.String(), nullable=True),
        sa.Column("inspiration_notes", sa.String(), nullable=True),
        sa.Column("avoid_notes", sa.String(), nullable=True),
        sa.Column("age_band", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("allow_reference_use", sa.Boolean(), nullable=False),
        sa.Column("approved_as_reference", sa.Boolean(), nullable=False),
        sa.Column("editorial_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_storysuggestion_age_band"), "storysuggestion", ["age_band"], unique=False)
    op.create_index(op.f("ix_storysuggestion_approved_as_reference"), "storysuggestion", ["approved_as_reference"], unique=False)
    op.create_index(op.f("ix_storysuggestion_child_profile_id"), "storysuggestion", ["child_profile_id"], unique=False)
    op.create_index(op.f("ix_storysuggestion_language"), "storysuggestion", ["language"], unique=False)
    op.create_index(op.f("ix_storysuggestion_status"), "storysuggestion", ["status"], unique=False)
    op.create_index(op.f("ix_storysuggestion_user_id"), "storysuggestion", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_storysuggestion_user_id"), table_name="storysuggestion")
    op.drop_index(op.f("ix_storysuggestion_status"), table_name="storysuggestion")
    op.drop_index(op.f("ix_storysuggestion_language"), table_name="storysuggestion")
    op.drop_index(op.f("ix_storysuggestion_child_profile_id"), table_name="storysuggestion")
    op.drop_index(op.f("ix_storysuggestion_approved_as_reference"), table_name="storysuggestion")
    op.drop_index(op.f("ix_storysuggestion_age_band"), table_name="storysuggestion")
    op.drop_table("storysuggestion")
