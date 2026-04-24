"""widen okr_objectives.quarter to String(64)

Revision ID: 010
Revises: 009
Create Date: 2026-04-22
"""
import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "okr_objectives",
        "quarter",
        existing_type=sa.String(8),
        type_=sa.String(64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "okr_objectives",
        "quarter",
        existing_type=sa.String(64),
        type_=sa.String(8),
        existing_nullable=False,
    )
