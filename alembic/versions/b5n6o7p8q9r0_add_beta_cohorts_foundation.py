"""add beta cohorts foundation

Revision ID: b5n6o7p8q9r0
Revises: a4m5n6o7p8q9
Create Date: 2026-03-16 22:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b5n6o7p8q9r0"
down_revision = "a4m5n6o7p8q9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "betacohort",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("feature_flag_keys", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("betacohort", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_betacohort_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_betacohort_key"), ["key"], unique=True)

    op.create_table(
        "betacohortmembership",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("beta_cohort_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("invited_by_user_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["beta_cohort_id"], ["betacohort.id"]),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("beta_cohort_id", "user_id", name="uq_betacohortmembership_cohort_user"),
    )
    with op.batch_alter_table("betacohortmembership", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_betacohortmembership_beta_cohort_id"), ["beta_cohort_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_betacohortmembership_invited_by_user_id"), ["invited_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_betacohortmembership_source"), ["source"], unique=False)
        batch_op.create_index(batch_op.f("ix_betacohortmembership_user_id"), ["user_id"], unique=False)

    with op.batch_alter_table("featureflag", schema=None) as batch_op:
        batch_op.add_column(sa.Column("target_beta_cohorts", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("featureflag", schema=None) as batch_op:
        batch_op.drop_column("target_beta_cohorts")

    with op.batch_alter_table("betacohortmembership", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_betacohortmembership_user_id"))
        batch_op.drop_index(batch_op.f("ix_betacohortmembership_source"))
        batch_op.drop_index(batch_op.f("ix_betacohortmembership_invited_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_betacohortmembership_beta_cohort_id"))

    op.drop_table("betacohortmembership")

    with op.batch_alter_table("betacohort", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_betacohort_key"))
        batch_op.drop_index(batch_op.f("ix_betacohort_created_by_user_id"))

    op.drop_table("betacohort")
