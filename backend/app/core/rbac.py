"""
RBAC 装饰器：permission_required
用于 Service 层函数，补充 API 层 Depends 的双重防护。
"""
import functools
from collections.abc import Callable

from app.core.exceptions import ForbiddenError


def permission_required(permission_code: str):
    """
    Service 层权限装饰器。传入已解析的 permissions: set[str]。

    用法：
        @permission_required("note:write")
        async def create_note(permissions: set[str], ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, permissions: set[str] | None = None, **kwargs):
            perms = permissions or set()
            if permission_code not in perms and "admin:all" not in perms:
                raise ForbiddenError(f"Missing permission: {permission_code}")
            return await func(*args, permissions=perms, **kwargs)
        return wrapper
    return decorator
