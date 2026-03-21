"""add privacy foundation

Revision ID: i4d5e6f7a8b9
Revises: h3c4d5e6f7a8
Create Date: 2026-03-13 18:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "i4d5e6f7a8b9"
down_revision = "h3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "legalacceptance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(), nullable=False),
        sa.Column("document_version", sa.String(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("legalacceptance", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_legalacceptance_document_type"), ["document_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_legalacceptance_user_id"), ["user_id"], unique=False)

    op.create_table(
        "privacypreference",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("marketing_email_opt_in", sa.Boolean(), nullable=False),
        sa.Column("product_updates_opt_in", sa.Boolean(), nullable=False),
        sa.Column("analytics_personalization_opt_in", sa.Boolean(), nullable=False),
        sa.Column("allow_recommendation_personalization", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("privacypreference", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_privacypreference_user_id"), ["user_id"], unique=True)

    op.create_table(
        "datarequest",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("child_profile_id", sa.Integer(), nullable=True),
        sa.Column("request_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("output_url", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["child_profile_id"], ["childprofile.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("datarequest", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_datarequest_child_profile_id"), ["child_profile_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_datarequest_request_type"), ["request_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_datarequest_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_datarequest_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("datarequest", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_datarequest_user_id"))
        batch_op.drop_index(batch_op.f("ix_datarequest_status"))
        batch_op.drop_index(batch_op.f("ix_datarequest_request_type"))
        batch_op.drop_index(batch_op.f("ix_datarequest_child_profile_id"))
    op.drop_table("datarequest")

    with op.batch_alter_table("privacypreference", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_privacypreference_user_id"))
    op.drop_table("privacypreference")

    with op.batch_alter_table("legalacceptance", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legalacceptance_user_id"))
        batch_op.drop_index(batch_op.f("ix_legalacceptance_document_type"))
    op.drop_table("legalacceptance")
