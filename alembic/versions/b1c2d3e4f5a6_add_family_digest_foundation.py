"""add family digest foundation

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-03-19 09:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b1c2d3e4f5a6"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "familydigest",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("digest_type", sa.String(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary_json", sa.String(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "digest_type",
            "period_start",
            "period_end",
            name="uq_family_digest_user_type_period",
        ),
    )
    with op.batch_alter_table("familydigest", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_familydigest_digest_type"), ["digest_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_familydigest_period_end"), ["period_end"], unique=False)
        batch_op.create_index(batch_op.f("ix_familydigest_period_start"), ["period_start"], unique=False)
        batch_op.create_index(batch_op.f("ix_familydigest_user_id"), ["user_id"], unique=False)

    op.create_table(
        "familydigestchildsummary",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_digest_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=False),
        sa.Column("stories_opened", sa.Integer(), nullable=False),
        sa.Column("stories_completed", sa.Integer(), nullable=False),
        sa.Column("narration_uses", sa.Integer(), nullable=False),
        sa.Column("achievements_earned", sa.Integer(), nullable=False),
        sa.Column("current_streak_days", sa.Integer(), nullable=False),
        sa.Column("summary_text", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["family_digest_id"], ["familydigest.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "family_digest_id",
            "child_profile_id",
            name="uq_family_digest_child_summary_digest_child",
        ),
    )
    with op.batch_alter_table("familydigestchildsummary", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_familydigestchildsummary_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_familydigestchildsummary_family_digest_id"), ["family_digest_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("familydigestchildsummary", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_familydigestchildsummary_family_digest_id"))
        batch_op.drop_index(batch_op.f("ix_familydigestchildsummary_child_profile_id"))
    op.drop_table("familydigestchildsummary")

    with op.batch_alter_table("familydigest", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_familydigest_user_id"))
        batch_op.drop_index(batch_op.f("ix_familydigest_period_start"))
        batch_op.drop_index(batch_op.f("ix_familydigest_period_end"))
        batch_op.drop_index(batch_op.f("ix_familydigest_digest_type"))
    op.drop_table("familydigest")
