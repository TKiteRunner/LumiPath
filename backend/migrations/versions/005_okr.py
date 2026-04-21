"""okr_objectives, okr_key_results, daily_tasks

Revision ID: 005
Revises: 004
Create Date: 2026-04-21
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "okr_objectives",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quarter", sa.String(8), nullable=False),
        sa.Column("priority", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("progress", sa.Numeric(5, 4), server_default="0", nullable=False),
        sa.Column("motivation", sa.Text(), nullable=True),
        sa.Column("success_picture", sa.Text(), nullable=True),
        sa.Column("vault_path", sa.String(512), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_okr_objectives_user_id", "okr_objectives", ["user_id"])

    op.create_table(
        "okr_key_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("objective_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("okr_objectives.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("metric", sa.String(128), nullable=True),
        sa.Column("baseline", sa.Numeric(), nullable=True),
        sa.Column("target", sa.Numeric(), nullable=True),
        sa.Column("current", sa.Numeric(), server_default="0", nullable=False),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("weight", sa.Numeric(3, 2), server_default="1.00", nullable=False),
        sa.Column("progress", sa.Numeric(5, 4), server_default="0", nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "daily_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kr_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("okr_key_results.id", ondelete="SET NULL"), nullable=True),
        sa.Column("task_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_done", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("done_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_daily_tasks_user_date", "daily_tasks", ["user_id", "task_date"])


def downgrade() -> None:
    op.drop_table("daily_tasks")
    op.drop_table("okr_key_results")
    op.drop_table("okr_objectives")
