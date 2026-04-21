"""companies, interviews, interview_questions, interview_reviews

Revision ID: 004
Revises: 003
Create Date: 2026-04-21
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("tier", sa.String(8), nullable=True),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(64), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_companies_slug"),
        sa.UniqueConstraint("name", "owner_id", name="uq_companies_name_owner"),
    )

    op.create_table(
        "interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("role", sa.String(128), nullable=False),
        sa.Column("round", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(16), server_default="scheduled", nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("interviewer", sa.String(128), nullable=True),
        sa.Column("format", sa.String(16), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("vault_path", sa.String(512), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(32)), server_default=sa.text("'{}'::varchar[]"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("round >= 1", name="ck_interview_round"),
    )
    op.create_index("ix_interviews_user_id", "interviews", ["user_id"])

    op.create_table(
        "interview_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("my_answer", sa.Text(), nullable=True),
        sa.Column("standard_answer", sa.Text(), nullable=True),
        sa.Column("gap_analysis", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.SmallInteger(), nullable=True),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(32)), server_default=sa.text("'{}'::varchar[]"), nullable=False),
        sa.Column("score", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_interview_questions_interview_id", "interview_questions", ["interview_id"])

    op.create_table(
        "interview_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("weaknesses", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("improvement_plan", sa.Text(), nullable=True),
        sa.Column("score_overall", sa.SmallInteger(), nullable=True),
        sa.Column("ai_model", sa.String(64), nullable=True),
        sa.Column("ai_tokens", sa.Integer(), nullable=True),
        sa.Column("ai_cost_usd", sa.Numeric(10, 4), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_table("interview_reviews")
    op.drop_table("interview_questions")
    op.drop_table("interviews")
    op.drop_table("companies")
