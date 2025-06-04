import logging
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class BusinessError(Exception):
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_id = str(uuid.uuid4())
    logger.error(
        f"Error ID: {error_id}, Path: {request.url.path}, Error: {str(exc)}",
        exc_info=True,
    )

    if isinstance(exc, BusinessError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_id": error_id,
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    if isinstance(exc, (RequestValidationError, ValidationError)):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_id": error_id,
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": exc.errors(),
            },
        )

    # 개발 환경에서만 상세 에러 표시
    is_debug = os.getenv("DEBUG", "false").lower() == "true"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_id": error_id,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": str(exc) if is_debug else None,
        },
    )


def register_error_handlers(app):
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(BusinessError, global_exception_handler)
    app.add_exception_handler(RequestValidationError, global_exception_handler)
