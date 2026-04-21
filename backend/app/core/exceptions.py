"""
统一异常类体系 + FastAPI exception handler 注册。
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


# ── 基础异常 ──────────────────────────────────────────────────────────────────
class LumiPathException(Exception):
    """所有业务异常的基类。"""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None, **kwargs):
        self.message = message or self.__class__.message
        self.extra = kwargs
        super().__init__(self.message)


# ── 4xx 异常 ──────────────────────────────────────────────────────────────────
class NotFoundError(LumiPathException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"
    message = "Resource not found"


class UnauthorizedError(LumiPathException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"
    message = "Authentication required"


class ForbiddenError(LumiPathException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"
    message = "Insufficient permissions"


class ConflictError(LumiPathException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"
    message = "Resource conflict (optimistic lock or duplicate)"


class ValidationError(LumiPathException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"
    message = "Validation failed"


class BadRequestError(LumiPathException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BAD_REQUEST"
    message = "Bad request"


# ── Agent / LLM 异常 ──────────────────────────────────────────────────────────
class LLMKeyNotFoundError(LumiPathException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "LLM_KEY_NOT_FOUND"
    message = "No valid LLM API key configured for this agent"


class AgentTimeoutError(LumiPathException):
    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    error_code = "AGENT_TIMEOUT"
    message = "Agent execution timed out"


# ── Vault 异常 ────────────────────────────────────────────────────────────────
class VaultConflictError(LumiPathException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "VAULT_CONFLICT"
    message = "File conflict detected in vault"


# ── Handler 注册 ──────────────────────────────────────────────────────────────
def register_exception_handlers(app: FastAPI) -> None:
    """在 FastAPI app 上注册统一异常响应格式。"""

    @app.exception_handler(LumiPathException)
    async def lumipath_exception_handler(request: Request, exc: LumiPathException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "detail": exc.extra or None,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "INTERNAL_ERROR", "message": str(exc)},
        )
