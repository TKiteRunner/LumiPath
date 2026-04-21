"""user_llm_keys, agent_llm_assignments, user_llm_key_usage

Revision ID: 003
Revises: 002
Create Date: 2026-04-21
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_llm_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("key_alias", sa.String(64), nullable=False),
        sa.Column("api_key_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("key_last4", sa.String(4), nullable=False),
        sa.Column("base_url", sa.String(512), nullable=True),
        sa.Column("default_model", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("monthly_budget_usd", sa.Numeric(10, 2), nullable=True),
        sa.Column("monthly_used_usd", sa.Numeric(10, 4), server_default="0", nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "provider", "key_alias", name="uq_llm_key_user_provider_alias"),
    )

    op.create_table(
        "agent_llm_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_name", sa.String(32), nullable=False),
        sa.Column("key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_llm_keys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "agent_name", name="uq_agent_assignment_user_agent"),
        sa.CheckConstraint(
            "agent_name IN ('supervisor', 'interview', 'okr', 'notes', 'memory')",
            name="ck_agent_name",
        ),
    )

    op.create_table(
        "user_llm_key_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_llm_keys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_llm_key_usage_key_id", "user_llm_key_usage", ["key_id"])
    op.create_index("ix_llm_key_usage_user_id", "user_llm_key_usage", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_llm_key_usage")
    op.drop_table("agent_llm_assignments")
    op.drop_table("user_llm_keys")
