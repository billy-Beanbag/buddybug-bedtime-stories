"""add organization team foundation

Revision ID: p3c4d5e6f7a8
Revises: o2b3c4d5e6f7
Create Date: 2026-03-15 22:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "p3c4d5e6f7a8"
down_revision = "o2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("organization", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_organization_slug"), ["slug"], unique=True)

    op.create_table(
        "organizationmembership",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_organization_membership"),
    )
    with op.batch_alter_table("organizationmembership", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_organizationmembership_organization_id"), ["organization_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_organizationmembership_role"), ["role"], unique=False)
        batch_op.create_index(batch_op.f("ix_organizationmembership_user_id"), ["user_id"], unique=False)

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_user_organization_id"), ["organization_id"], unique=False)
        batch_op.create_foreign_key("fk_user_organization_id_organization", "organization", ["organization_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint("fk_user_organization_id_organization", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_user_organization_id"))
        batch_op.drop_column("organization_id")

    with op.batch_alter_table("organizationmembership", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_organizationmembership_user_id"))
        batch_op.drop_index(batch_op.f("ix_organizationmembership_role"))
        batch_op.drop_index(batch_op.f("ix_organizationmembership_organization_id"))

    op.drop_table("organizationmembership")

    with op.batch_alter_table("organization", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_organization_slug"))

    op.drop_table("organization")
