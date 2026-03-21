"""add story validation to review queue

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-03-17 13:50:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b0c1d2e3f4a5"
down_revision = "a9b0c1d2e3f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("storyreviewqueue", schema=None) as batch_op:
        batch_op.add_column(sa.Column("story_validation", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("storyreviewqueue", schema=None) as batch_op:
        batch_op.drop_column("story_validation")
