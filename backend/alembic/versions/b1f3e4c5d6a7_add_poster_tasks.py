"""add poster_tasks

Revision ID: b1f3e4c5d6a7
Revises: 2a0d392ab099
Create Date: 2026-06-02 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1f3e4c5d6a7"
down_revision: Union[str, Sequence[str], None] = "2a0d392ab099"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "poster_tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("size", sa.String(length=32), nullable=False),
        sa.Column("model_used", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_poster_tasks_created_at"),
        "poster_tasks",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_poster_tasks_status"),
        "poster_tasks",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_poster_tasks_user_id"),
        "poster_tasks",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_poster_tasks_user_id"), table_name="poster_tasks")
    op.drop_index(op.f("ix_poster_tasks_status"), table_name="poster_tasks")
    op.drop_index(op.f("ix_poster_tasks_created_at"), table_name="poster_tasks")
    op.drop_table("poster_tasks")
