"""vault_configs, notes, note_tags, note_links, note_embeddings, conflicts

Revision ID: 006
Revises: 005
Create Date: 2026-04-21
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vault_configs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("vault_path", sa.String(512), nullable=False),
        sa.Column("git_remote_url", sa.String(512), nullable=True),
        sa.Column("git_credentials_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("git_credential_type", sa.String(16), nullable=True),
        sa.Column("auto_commit", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("auto_push", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("commit_debounce_sec", sa.Integer(), server_default="10", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path", sa.String(512), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("note_date", sa.Date(), nullable=True),
        sa.Column("frontmatter", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("content_preview", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("file_mtime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_private", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kr_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("okr_key_results.id", ondelete="SET NULL"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "path", name="uq_notes_user_path"),
    )
    op.create_index("ix_notes_user_id", "notes", ["user_id"])
    op.create_index("ix_notes_type", "notes", ["type"])
    op.execute("CREATE INDEX ix_notes_title_trgm ON notes USING gin (title gin_trgm_ops) WHERE title IS NOT NULL")

    op.create_table(
        "note_tags",
        sa.Column("note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag", sa.String(64), primary_key=True),
    )
    op.create_index("ix_note_tags_tag", "note_tags", ["tag"])

    op.create_table(
        "note_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("source_note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_slug", sa.String(255), nullable=True),
        sa.Column("anchor", sa.String(255), nullable=True),
        sa.Column("display_text", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "note_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.SmallInteger(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("note_id", "chunk_index", "model_name", name="uq_note_embedding_chunk"),
    )
    # pgvector column added separately since SQLAlchemy doesn't natively render vector(n)
    op.execute("ALTER TABLE note_embeddings ADD COLUMN embedding vector(1536)")
    op.execute("CREATE INDEX ix_note_embeddings_hnsw ON note_embeddings USING hnsw (embedding vector_cosine_ops)")

    op.create_table(
        "conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("resolution", sa.String(16), nullable=True),
        sa.Column("conflict_file", sa.String(512), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("conflicts")
    op.drop_table("note_embeddings")
    op.drop_table("note_links")
    op.drop_table("note_tags")
    op.drop_table("notes")
    op.drop_table("vault_configs")
