"""seed: initial roles and permissions

Revision ID: 009
Revises: 008
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None

_ROLES = [
    ("user", "Regular authenticated user"),
    ("admin", "System administrator"),
]

_PERMISSIONS = [
    ("interview:read", "View interviews"),
    ("interview:write", "Create and edit interviews"),
    ("okr:read", "View OKR objectives"),
    ("okr:write", "Create and edit OKR objectives"),
    ("note:read", "View notes"),
    ("note:write", "Create and edit notes"),
    ("agent:chat", "Use the AI agent"),
    ("admin:all", "Full admin access"),
]

_USER_PERMISSIONS = [p[0] for p in _PERMISSIONS if not p[0].startswith("admin")]
_ADMIN_PERMISSIONS = [p[0] for p in _PERMISSIONS]


def upgrade() -> None:
    conn = op.get_bind()

    # Insert roles
    roles_table = sa.table("roles", sa.column("name"), sa.column("description"))
    op.bulk_insert(roles_table, [{"name": name, "description": desc} for name, desc in _ROLES])

    # Insert permissions
    perms_table = sa.table("permissions", sa.column("code"), sa.column("description"))
    op.bulk_insert(perms_table, [{"code": code, "description": desc} for code, desc in _PERMISSIONS])

    # Assign permissions to roles
    role_perms_table = sa.table("role_permissions", sa.column("role_id"), sa.column("permission_id"))
    for role_name, perm_codes in [("user", _USER_PERMISSIONS), ("admin", _ADMIN_PERMISSIONS)]:
        role_id = conn.execute(
            sa.text("SELECT id FROM roles WHERE name = :name"), {"name": role_name}
        ).scalar()
        for code in perm_codes:
            perm_id = conn.execute(
                sa.text("SELECT id FROM permissions WHERE code = :code"), {"code": code}
            ).scalar()
            conn.execute(
                sa.text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :perm_id)"),
                {"role_id": str(role_id), "perm_id": str(perm_id)},
            )


def downgrade() -> None:
    op.execute("DELETE FROM role_permissions")
    op.execute("DELETE FROM permissions")
    op.execute("DELETE FROM roles")
