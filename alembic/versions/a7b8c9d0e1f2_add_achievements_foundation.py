"""add achievements foundation

Revision ID: a7b8c9d0e1f2
Revises: f2a3b4c5d6e7
Create Date: 2026-03-18 18:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a7b8c9d0e1f2"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "achievementdefinition",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("icon_key", sa.String(), nullable=True),
        sa.Column("target_scope", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("achievementdefinition", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_achievementdefinition_key"), ["key"], unique=True)
        batch_op.create_index(batch_op.f("ix_achievementdefinition_target_scope"), ["target_scope"], unique=False)

    op.create_table(
        "earnedachievement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("achievement_definition_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("earned_at", sa.DateTime(), nullable=False),
        sa.Column("source_table", sa.String(), nullable=True),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["achievement_definition_id"], ["achievementdefinition.id"]),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "achievement_definition_id",
            "user_id",
            "child_profile_id",
            name="uq_earned_achievement_definition_user_child",
        ),
    )
    with op.batch_alter_table("earnedachievement", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_earnedachievement_achievement_definition_id"), ["achievement_definition_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_earnedachievement_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_earnedachievement_user_id"), ["user_id"], unique=False)

    op.create_table(
        "readingstreaksnapshot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("current_streak_days", sa.Integer(), nullable=False),
        sa.Column("longest_streak_days", sa.Integer(), nullable=False),
        sa.Column("last_read_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "child_profile_id", name="uq_reading_streak_snapshot_user_child"),
    )
    with op.batch_alter_table("readingstreaksnapshot", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_readingstreaksnapshot_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_readingstreaksnapshot_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("readingstreaksnapshot", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_readingstreaksnapshot_user_id"))
        batch_op.drop_index(batch_op.f("ix_readingstreaksnapshot_child_profile_id"))
    op.drop_table("readingstreaksnapshot")

    with op.batch_alter_table("earnedachievement", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_earnedachievement_user_id"))
        batch_op.drop_index(batch_op.f("ix_earnedachievement_child_profile_id"))
        batch_op.drop_index(batch_op.f("ix_earnedachievement_achievement_definition_id"))
    op.drop_table("earnedachievement")

    with op.batch_alter_table("achievementdefinition", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_achievementdefinition_target_scope"))
        batch_op.drop_index(batch_op.f("ix_achievementdefinition_key"))
    op.drop_table("achievementdefinition")
