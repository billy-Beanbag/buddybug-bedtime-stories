"""add reengagement foundation

Revision ID: l7g8h9i0j1k2
Revises: k6f7a8b9c0d1
Create Date: 2026-03-15 10:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "l7g8h9i0j1k2"
down_revision = "k6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "userengagementstate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("state_key", sa.String(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(), nullable=True),
        sa.Column("last_story_opened_at", sa.DateTime(), nullable=True),
        sa.Column("last_story_completed_at", sa.DateTime(), nullable=True),
        sa.Column("last_subscription_active_at", sa.DateTime(), nullable=True),
        sa.Column("active_child_profiles_count", sa.Integer(), nullable=False),
        sa.Column("unread_saved_books_count", sa.Integer(), nullable=False),
        sa.Column("unfinished_books_count", sa.Integer(), nullable=False),
        sa.Column("preview_only_books_count", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("userengagementstate", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_userengagementstate_state_key"), ["state_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_userengagementstate_user_id"), ["user_id"], unique=True)

    op.create_table(
        "reengagementsuggestion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("suggestion_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("related_book_id", sa.Integer(), nullable=True),
        sa.Column("state_key", sa.String(), nullable=True),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["related_book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("reengagementsuggestion", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_reengagementsuggestion_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_reengagementsuggestion_related_book_id"), ["related_book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_reengagementsuggestion_state_key"), ["state_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_reengagementsuggestion_suggestion_type"), ["suggestion_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_reengagementsuggestion_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("reengagementsuggestion", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_reengagementsuggestion_user_id"))
        batch_op.drop_index(batch_op.f("ix_reengagementsuggestion_suggestion_type"))
        batch_op.drop_index(batch_op.f("ix_reengagementsuggestion_state_key"))
        batch_op.drop_index(batch_op.f("ix_reengagementsuggestion_related_book_id"))
        batch_op.drop_index(batch_op.f("ix_reengagementsuggestion_child_profile_id"))

    op.drop_table("reengagementsuggestion")

    with op.batch_alter_table("userengagementstate", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_userengagementstate_user_id"))
        batch_op.drop_index(batch_op.f("ix_userengagementstate_state_key"))

    op.drop_table("userengagementstate")
