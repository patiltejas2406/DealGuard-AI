"""Domain Exceptions and Global Exception Handlers."""

import traceback
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("dealguard.exceptions")


class DealGuardException(Exception):
    """Base domain exception for DealGuard AI."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(DealGuardException):
    """Resource not found exception."""

    def __init__(self, resource: str, resource_id: Any, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource} with identifier '{resource_id}' was not found.",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class UnauthorizedException(DealGuardException):
    """Authentication failure exception."""

    def __init__(self, message: str = "Authentication required or invalid credentials.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenException(DealGuardException):
    """Authorization / RBAC failure exception."""

    def __init__(self, message: str = "Access to this resource is forbidden.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ValidationException(DealGuardException):
    """Business rule validation failure."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class ConflictException(DealGuardException):
    """Resource state conflict (e.g. duplicate key)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class PromptInjectionException(DealGuardException):
    """Detected adversarial instruction injection in document data."""

    def __init__(self, message: str = "Document content contains prohibited prompt injection patterns.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="SECURITY_PROMPT_INJECTION_DETECTED",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform JSON error response handlers across the application."""

    @app.exception_handler(DealGuardException)
    async def dealguard_exception_handler(request: Request, exc: DealGuardException) -> JSONResponse:
        logger.warning(
            f"Handled DealGuardException: {exc.message}",
            extra={
                "error_code": exc.code,
                "error_message": exc.message,
                "status_code": exc.status_code,
                "path": request.url.path,
                "error_details": exc.details,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        logger.warning(
            "Request validation error",
            extra={"path": request.url.path, "errors": errors}
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "REQUEST_VALIDATION_ERROR",
                    "message": "The submitted payload failed schema validation.",
                    "details": {"validation_errors": errors},
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": str(exc.detail),
                    "details": {},
                }
            }
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        tb = traceback.format_exc()
        logger.error(
            "Unhandled system exception",
            extra={"path": request.url.path, "error": str(exc), "traceback": tb}
        )
        message = "An unexpected internal server error occurred."
        details: Dict[str, Any] = {}
        if settings.DEBUG:
            details = {"error_type": type(exc).__name__, "error_detail": str(exc)}

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": message,
                    "details": details,
                }
            }
        )
