"""add classics workflow foundation

Revision ID: r8s9t0u1v2w3
Revises: q7r8s9t0u1v2
Create Date: 2026-04-04 10:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "r8s9t0u1v2w3"
down_revision = "q7r8s9t0u1v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "classicsource",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_text", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("public_domain_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_author", sa.String(), nullable=True),
        sa.Column("source_origin_notes", sa.String(), nullable=True),
        sa.Column("import_status", sa.String(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("classicsource", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_classicsource_title"), ["title"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicsource_public_domain_verified"), ["public_domain_verified"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicsource_import_status"), ["import_status"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicsource_created_by_user_id"), ["created_by_user_id"], unique=False)

    with op.batch_alter_table("storydraft", schema=None) as batch_op:
        batch_op.add_column(sa.Column("classic_source_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("is_classic", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_foreign_key(
            "fk_storydraft_classic_source_id_classicsource",
            "classicsource",
            ["classic_source_id"],
            ["id"],
        )
        batch_op.create_index(batch_op.f("ix_storydraft_classic_source_id"), ["classic_source_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_storydraft_is_classic"), ["is_classic"], unique=False)

    with op.batch_alter_table("book", schema=None) as batch_op:
        batch_op.add_column(sa.Column("classic_source_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("is_classic", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_foreign_key(
            "fk_book_classic_source_id_classicsource",
            "classicsource",
            ["classic_source_id"],
            ["id"],
        )
        batch_op.create_index(batch_op.f("ix_book_classic_source_id"), ["classic_source_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_book_is_classic"), ["is_classic"], unique=False)

    op.create_table(
        "classicadaptationdraft",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("classic_source_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("story_draft_id", sa.Integer(), nullable=True),
        sa.Column("preview_book_id", sa.Integer(), nullable=True),
        sa.Column("adapted_title", sa.String(), nullable=False),
        sa.Column("adapted_text", sa.String(), nullable=False),
        sa.Column("adaptation_intensity", sa.String(), nullable=False, server_default="light"),
        sa.Column("adaptation_notes", sa.String(), nullable=True),
        sa.Column("cameo_insertions_summary", sa.String(), nullable=True),
        sa.Column("scene_seed_notes_json", sa.String(), nullable=True),
        sa.Column("page_scene_data_json", sa.String(), nullable=True),
        sa.Column("validation_status", sa.String(), nullable=False, server_default="accepted"),
        sa.Column("validation_warnings_json", sa.String(), nullable=True),
        sa.Column("illustration_status", sa.String(), nullable=False),
        sa.Column("review_status", sa.String(), nullable=False),
        sa.Column("editor_notes", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["classic_source_id"], ["classicsource.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["preview_book_id"], ["book.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["editorialproject.id"]),
        sa.ForeignKeyConstraint(["story_draft_id"], ["storydraft.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("classicadaptationdraft", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_classic_source_id"), ["classic_source_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_project_id"), ["project_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_story_draft_id"), ["story_draft_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_preview_book_id"), ["preview_book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_adapted_title"), ["adapted_title"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_adaptation_intensity"), ["adaptation_intensity"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_validation_status"), ["validation_status"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_illustration_status"), ["illustration_status"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_review_status"), ["review_status"], unique=False)
        batch_op.create_index(batch_op.f("ix_classicadaptationdraft_created_by_user_id"), ["created_by_user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("classicadaptationdraft", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_review_status"))
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_illustration_status"))
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_validation_status"))
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_adaptation_intensity"))
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_adapted_title"))
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_preview_book_id"))
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_story_draft_id"))
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_project_id"))
        batch_op.drop_index(batch_op.f("ix_classicadaptationdraft_classic_source_id"))
    op.drop_table("classicadaptationdraft")

    with op.batch_alter_table("book", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_book_is_classic"))
        batch_op.drop_index(batch_op.f("ix_book_classic_source_id"))
        batch_op.drop_constraint("fk_book_classic_source_id_classicsource", type_="foreignkey")
        batch_op.drop_column("is_classic")
        batch_op.drop_column("classic_source_id")

    with op.batch_alter_table("storydraft", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storydraft_is_classic"))
        batch_op.drop_index(batch_op.f("ix_storydraft_classic_source_id"))
        batch_op.drop_constraint("fk_storydraft_classic_source_id_classicsource", type_="foreignkey")
        batch_op.drop_column("is_classic")
        batch_op.drop_column("classic_source_id")

    with op.batch_alter_table("classicsource", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_classicsource_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_classicsource_import_status"))
        batch_op.drop_index(batch_op.f("ix_classicsource_public_domain_verified"))
        batch_op.drop_index(batch_op.f("ix_classicsource_title"))
    op.drop_table("classicsource")
