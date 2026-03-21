"""add editorial tools foundation

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-03-13 12:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_editor", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "editorialproject",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("age_band", sa.String(), nullable=False),
        sa.Column("content_lane_key", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_editor_user_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_editor_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    with op.batch_alter_table("editorialproject", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_editorialproject_title"), ["title"], unique=False)
        batch_op.create_index(batch_op.f("ix_editorialproject_slug"), ["slug"], unique=True)
        batch_op.create_index(batch_op.f("ix_editorialproject_age_band"), ["age_band"], unique=False)
        batch_op.create_index(batch_op.f("ix_editorialproject_content_lane_key"), ["content_lane_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_editorialproject_language"), ["language"], unique=False)
        batch_op.create_index(batch_op.f("ix_editorialproject_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_editorialproject_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_editorialproject_assigned_editor_user_id"), ["assigned_editor_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_editorialproject_source_type"), ["source_type"], unique=False)

    op.create_table(
        "editorialasset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["editorialproject.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("editorialasset", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_editorialasset_project_id"), ["project_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_editorialasset_asset_type"), ["asset_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_editorialasset_created_by_user_id"), ["created_by_user_id"], unique=False)

    with op.batch_alter_table("storydraft", schema=None) as batch_op:
        batch_op.alter_column("story_idea_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("project_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("age_band", sa.String(), nullable=False, server_default="3-7"))
        batch_op.add_column(sa.Column("language", sa.String(), nullable=False, server_default="en"))
        batch_op.create_foreign_key(
            "fk_storydraft_project_id_editorialproject",
            "editorialproject",
            ["project_id"],
            ["id"],
        )
        batch_op.create_index(batch_op.f("ix_storydraft_project_id"), ["project_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_storydraft_age_band"), ["age_band"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("storydraft", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storydraft_age_band"))
        batch_op.drop_index(batch_op.f("ix_storydraft_project_id"))
        batch_op.drop_constraint("fk_storydraft_project_id_editorialproject", type_="foreignkey")
        batch_op.drop_column("language")
        batch_op.drop_column("age_band")
        batch_op.drop_column("project_id")
        batch_op.alter_column("story_idea_id", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("editorialasset", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_editorialasset_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_editorialasset_asset_type"))
        batch_op.drop_index(batch_op.f("ix_editorialasset_project_id"))
    op.drop_table("editorialasset")

    with op.batch_alter_table("editorialproject", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_editorialproject_source_type"))
        batch_op.drop_index(batch_op.f("ix_editorialproject_assigned_editor_user_id"))
        batch_op.drop_index(batch_op.f("ix_editorialproject_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_editorialproject_status"))
        batch_op.drop_index(batch_op.f("ix_editorialproject_language"))
        batch_op.drop_index(batch_op.f("ix_editorialproject_content_lane_key"))
        batch_op.drop_index(batch_op.f("ix_editorialproject_age_band"))
        batch_op.drop_index(batch_op.f("ix_editorialproject_slug"))
        batch_op.drop_index(batch_op.f("ix_editorialproject_title"))
    op.drop_table("editorialproject")

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("is_editor")
