"""add child profiles foundation

Revision ID: f6a7b8c9d0e1
Revises: e5f2a1b9c8d7
Create Date: 2026-03-13 12:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision = "f6a7b8c9d0e1"
down_revision = "e5f2a1b9c8d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "childprofile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("age_band", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("language", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("content_lane_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("childprofile", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_childprofile_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_childprofile_age_band"), ["age_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_childprofile_content_lane_key"), ["content_lane_key"], unique=False)

    op.create_table(
        "childreadingprofile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=False),
        sa.Column("favorite_characters", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("preferred_tones", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("preferred_lengths", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("preferred_settings", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("preferred_styles", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("total_books_completed", sa.Integer(), nullable=False),
        sa.Column("total_books_replayed", sa.Integer(), nullable=False),
        sa.Column("last_profile_refresh_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("childreadingprofile", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_childreadingprofile_child_profile_id"), ["child_profile_id"], unique=True)

    with op.batch_alter_table("readingprogress", schema=None) as batch_op:
        batch_op.drop_constraint("uq_reader_book_progress", type_="unique")
        batch_op.add_column(sa.Column("child_profile_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_readingprogress_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_readingprogress_child_profile_id_childprofile",
            "childprofile",
            ["child_profile_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_reader_book_child_progress",
            ["reader_identifier", "book_id", "child_profile_id"],
        )

    with op.batch_alter_table("userstoryfeedback", schema=None) as batch_op:
        batch_op.drop_constraint("uq_user_book_feedback", type_="unique")
        batch_op.add_column(sa.Column("child_profile_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_userstoryfeedback_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_userstoryfeedback_child_profile_id_childprofile",
            "childprofile",
            ["child_profile_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_user_book_child_feedback",
            ["user_id", "book_id", "child_profile_id"],
        )

    with op.batch_alter_table("analyticsevent", schema=None) as batch_op:
        batch_op.add_column(sa.Column("child_profile_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_analyticsevent_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_analyticsevent_child_profile_id_childprofile",
            "childprofile",
            ["child_profile_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("analyticsevent", schema=None) as batch_op:
        batch_op.drop_constraint("fk_analyticsevent_child_profile_id_childprofile", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_analyticsevent_child_profile_id"))
        batch_op.drop_column("child_profile_id")

    with op.batch_alter_table("userstoryfeedback", schema=None) as batch_op:
        batch_op.drop_constraint("uq_user_book_child_feedback", type_="unique")
        batch_op.drop_constraint("fk_userstoryfeedback_child_profile_id_childprofile", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_userstoryfeedback_child_profile_id"))
        batch_op.drop_column("child_profile_id")
        batch_op.create_unique_constraint("uq_user_book_feedback", ["user_id", "book_id"])

    with op.batch_alter_table("readingprogress", schema=None) as batch_op:
        batch_op.drop_constraint("uq_reader_book_child_progress", type_="unique")
        batch_op.drop_constraint("fk_readingprogress_child_profile_id_childprofile", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_readingprogress_child_profile_id"))
        batch_op.drop_column("child_profile_id")
        batch_op.create_unique_constraint("uq_reader_book_progress", ["reader_identifier", "book_id"])

    with op.batch_alter_table("childreadingprofile", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_childreadingprofile_child_profile_id"))
    op.drop_table("childreadingprofile")

    with op.batch_alter_table("childprofile", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_childprofile_content_lane_key"))
        batch_op.drop_index(batch_op.f("ix_childprofile_age_band"))
        batch_op.drop_index(batch_op.f("ix_childprofile_user_id"))
    op.drop_table("childprofile")
