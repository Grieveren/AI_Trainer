"""Error handling middleware."""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """Middleware for handling application errors."""

    def __init__(self, app):
        """Initialize error handling middleware."""
        self.app = app

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors."""
        try:
            response = await call_next(request)
            return response

        except IntegrityError as exc:
            logger.error(f"Database integrity error: {exc}")
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "detail": "Resource conflict. This record may already exist.",
                    "type": "integrity_error",
                },
            )

        except SQLAlchemyError as exc:
            logger.error(f"Database error: {exc}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Database error occurred.",
                    "type": "database_error",
                },
            )

        except ValueError as exc:
            logger.warning(f"Validation error: {exc}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "detail": str(exc),
                    "type": "validation_error",
                },
            )

        except PermissionError as exc:
            logger.warning(f"Permission denied: {exc}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Permission denied.",
                    "type": "permission_error",
                },
            )

        except Exception as exc:
            logger.exception(f"Unhandled error: {exc}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "An unexpected error occurred.",
                    "type": "internal_error",
                },
            )


def setup_error_handling(app):
    """Add error handling middleware to FastAPI app."""
    app.add_middleware(ErrorHandlingMiddleware)
