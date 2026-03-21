"""add read along foundation

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-03-18 14:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "readalongsession",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("join_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("current_page_number", sa.Integer(), nullable=False),
        sa.Column("playback_state", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("readalongsession", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_readalongsession_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_readalongsession_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_readalongsession_join_code"), ["join_code"], unique=True)
        batch_op.create_index(batch_op.f("ix_readalongsession_language"), ["language"], unique=False)
        batch_op.create_index(batch_op.f("ix_readalongsession_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_readalongsession_user_id"), ["user_id"], unique=False)

    op.create_table(
        "readalongparticipant",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["readalongsession.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "user_id",
            "child_profile_id",
            name="uq_read_along_participant_session_user_child",
        ),
    )
    with op.batch_alter_table("readalongparticipant", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_readalongparticipant_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_readalongparticipant_role"), ["role"], unique=False)
        batch_op.create_index(batch_op.f("ix_readalongparticipant_session_id"), ["session_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_readalongparticipant_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("readalongparticipant", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_readalongparticipant_user_id"))
        batch_op.drop_index(batch_op.f("ix_readalongparticipant_session_id"))
        batch_op.drop_index(batch_op.f("ix_readalongparticipant_role"))
        batch_op.drop_index(batch_op.f("ix_readalongparticipant_child_profile_id"))

    op.drop_table("readalongparticipant")

    with op.batch_alter_table("readalongsession", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_readalongsession_user_id"))
        batch_op.drop_index(batch_op.f("ix_readalongsession_status"))
        batch_op.drop_index(batch_op.f("ix_readalongsession_language"))
        batch_op.drop_index(batch_op.f("ix_readalongsession_join_code"))
        batch_op.drop_index(batch_op.f("ix_readalongsession_child_profile_id"))
        batch_op.drop_index(batch_op.f("ix_readalongsession_book_id"))

    op.drop_table("readalongsession")
