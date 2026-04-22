"""agent_sessions, agent_messages, memory_long_term, memory_long_term_history,
memory_summaries, memory_episodes, memory_procedures, tools_registry

Revision ID: 007
Revises: 006
Create Date: 2026-04-21
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("thread_id", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("context_type", sa.String(32), nullable=True),
        sa.Column("context_ref", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("model_name", sa.String(64), nullable=True),
        sa.Column("llm_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_llm_keys.id", ondelete="SET NULL"), nullable=True),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_cost_usd", sa.Numeric(10, 4), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agent_sessions_user_id", "agent_sessions", ["user_id"])

    op.create_table(
        "agent_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("tool_calls", postgresql.JSONB(), nullable=True),
        sa.Column("tool_call_id", sa.String(128), nullable=True),
        sa.Column("tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("node_name", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agent_messages_session_id", "agent_messages", ["session_id"])

    op.create_table(
        "memory_long_term",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("profile", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("ability_model", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("preferences", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "memory_long_term_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("diff", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "memory_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(64), nullable=True),
        sa.Column("tokens_saved", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("ALTER TABLE memory_summaries ADD COLUMN embedding vector(1536)")
    op.execute("CREATE INDEX ix_memory_summaries_hnsw ON memory_summaries USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL")

    op.create_table(
        "memory_episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("context", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(64), nullable=True),
        sa.Column("linked_notes", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default=sa.text("'{}'::uuid[]"), nullable=False),
        sa.Column("linked_interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True),
        sa.Column("importance", sa.SmallInteger(), server_default="5", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("ALTER TABLE memory_episodes ADD COLUMN embedding vector(1536)")
    op.execute("CREATE INDEX ix_memory_episodes_hnsw ON memory_episodes USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL")
    op.create_index("ix_memory_episodes_user_id", "memory_episodes", ["user_id"])

    op.create_table(
        "memory_procedures",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("tool_version", sa.String(16), nullable=True),
        sa.Column("input", postgresql.JSONB(), nullable=True),
        sa.Column("output", postgresql.JSONB(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("review", sa.Text(), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_memory_procedures_user_tool", "memory_procedures", ["user_id", "tool_name"])

    op.create_table(
        "tools_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("version", sa.String(16), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("input_schema", postgresql.JSONB(), nullable=True),
        sa.Column("output_schema", postgresql.JSONB(), nullable=True),
        sa.Column("category", sa.String(32), nullable=True),
        sa.Column("requires_llm", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_unique_constraint("uq_tools_registry_name_version", "tools_registry", ["name", "version"])


def downgrade() -> None:
    op.drop_table("tools_registry")
    op.drop_table("memory_procedures")
    op.drop_table("memory_episodes")
    op.drop_table("memory_summaries")
    op.drop_table("memory_long_term_history")
    op.drop_table("memory_long_term")
    op.drop_table("agent_messages")
    op.drop_table("agent_sessions")
