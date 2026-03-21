"""add analytics tables

Revision ID: d4e7f1c2b3a4
Revises: c3f4d8e9a1b2
Create Date: 2026-03-13 00:35:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = "d4e7f1c2b3a4"
down_revision = "c3f4d8e9a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analyticsevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("reader_identifier", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("book_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("language", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("country", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("experiment_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("experiment_variant", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("metadata_json", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("analyticsevent", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_analyticsevent_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_analyticsevent_country"), ["country"], unique=False)
        batch_op.create_index(batch_op.f("ix_analyticsevent_event_name"), ["event_name"], unique=False)
        batch_op.create_index(batch_op.f("ix_analyticsevent_experiment_key"), ["experiment_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_analyticsevent_language"), ["language"], unique=False)
        batch_op.create_index(batch_op.f("ix_analyticsevent_occurred_at"), ["occurred_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_analyticsevent_reader_identifier"), ["reader_identifier"], unique=False)
        batch_op.create_index(batch_op.f("ix_analyticsevent_session_id"), ["session_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_analyticsevent_user_id"), ["user_id"], unique=False)

    op.create_table(
        "experimentassignment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("experiment_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("reader_identifier", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("variant", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("experimentassignment", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_experimentassignment_experiment_key"), ["experiment_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_experimentassignment_reader_identifier"), ["reader_identifier"], unique=False)
        batch_op.create_index(batch_op.f("ix_experimentassignment_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("experimentassignment", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_experimentassignment_user_id"))
        batch_op.drop_index(batch_op.f("ix_experimentassignment_reader_identifier"))
        batch_op.drop_index(batch_op.f("ix_experimentassignment_experiment_key"))

    op.drop_table("experimentassignment")

    with op.batch_alter_table("analyticsevent", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_analyticsevent_user_id"))
        batch_op.drop_index(batch_op.f("ix_analyticsevent_session_id"))
        batch_op.drop_index(batch_op.f("ix_analyticsevent_reader_identifier"))
        batch_op.drop_index(batch_op.f("ix_analyticsevent_occurred_at"))
        batch_op.drop_index(batch_op.f("ix_analyticsevent_language"))
        batch_op.drop_index(batch_op.f("ix_analyticsevent_experiment_key"))
        batch_op.drop_index(batch_op.f("ix_analyticsevent_event_name"))
        batch_op.drop_index(batch_op.f("ix_analyticsevent_country"))
        batch_op.drop_index(batch_op.f("ix_analyticsevent_book_id"))

    op.drop_table("analyticsevent")
