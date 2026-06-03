"""add video_tasks

Revision ID: c3f2d1a9b8e7
Revises: b1f3e4c5d6a7
Create Date: 2026-06-02 19:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3f2d1a9b8e7"
down_revision: Union[str, Sequence[str], None] = "b1f3e4c5d6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "video_tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("shot_count", sa.Integer(), nullable=False),
        sa.Column("script_model", sa.String(length=100), nullable=False),
        sa.Column("image_model", sa.String(length=100), nullable=False),
        sa.Column("clip_model", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("stage", sa.String(length=24), nullable=False),
        sa.Column("script_data", sa.JSON(), nullable=True),
        sa.Column("image_urls", sa.JSON(), nullable=True),
        sa.Column("clip_urls", sa.JSON(), nullable=True),
        sa.Column("final_video_url", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_video_tasks_created_at"),
        "video_tasks",
        ["created_at"],
        unique=False,
    )
    op.create_index(op.f("ix_video_tasks_stage"), "video_tasks", ["stage"], unique=False)
    op.create_index(
        op.f("ix_video_tasks_status"),
        "video_tasks",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_video_tasks_user_id"),
        "video_tasks",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_video_tasks_user_id"), table_name="video_tasks")
    op.drop_index(op.f("ix_video_tasks_status"), table_name="video_tasks")
    op.drop_index(op.f("ix_video_tasks_stage"), table_name="video_tasks")
    op.drop_index(op.f("ix_video_tasks_created_at"), table_name="video_tasks")
    op.drop_table("video_tasks")
