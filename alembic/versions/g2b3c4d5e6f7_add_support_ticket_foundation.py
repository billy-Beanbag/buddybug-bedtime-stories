"""add support ticket foundation

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-03-13 14:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "g2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supportticket",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("related_book_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["related_book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("supportticket", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_supportticket_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_supportticket_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_supportticket_category"), ["category"], unique=False)
        batch_op.create_index(batch_op.f("ix_supportticket_related_book_id"), ["related_book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_supportticket_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_supportticket_priority"), ["priority"], unique=False)
        batch_op.create_index(batch_op.f("ix_supportticket_assigned_to_user_id"), ["assigned_to_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_supportticket_source"), ["source"], unique=False)

    op.create_table(
        "supportticketnote",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=True),
        sa.Column("note_type", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["supportticket.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("supportticketnote", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_supportticketnote_ticket_id"), ["ticket_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_supportticketnote_author_user_id"), ["author_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_supportticketnote_note_type"), ["note_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("supportticketnote", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_supportticketnote_note_type"))
        batch_op.drop_index(batch_op.f("ix_supportticketnote_author_user_id"))
        batch_op.drop_index(batch_op.f("ix_supportticketnote_ticket_id"))
    op.drop_table("supportticketnote")

    with op.batch_alter_table("supportticket", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_supportticket_source"))
        batch_op.drop_index(batch_op.f("ix_supportticket_assigned_to_user_id"))
        batch_op.drop_index(batch_op.f("ix_supportticket_priority"))
        batch_op.drop_index(batch_op.f("ix_supportticket_status"))
        batch_op.drop_index(batch_op.f("ix_supportticket_related_book_id"))
        batch_op.drop_index(batch_op.f("ix_supportticket_category"))
        batch_op.drop_index(batch_op.f("ix_supportticket_child_profile_id"))
        batch_op.drop_index(batch_op.f("ix_supportticket_user_id"))
    op.drop_table("supportticket")
