"""API Middleware Module.

Provides correlation ID propagation (X-Request-ID) and structured request logging.
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger("app.middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware for propagating X-Request-ID and recording request metrics."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract or generate a clean request ID
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Attach request id back to response headers
            response.headers["X-Request-ID"] = request_id

            # Log request metrics
            if request.url.path not in ("/health", "/ready"):
                logger.info(
                    f"{request.method} {request.url.path} completed with {response.status_code} in {duration_ms}ms",
                    extra={
                        "request_id": request_id,
                        "duration_ms": duration_ms,
                    },
                )
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled exception on {request.method} {request.url.path}: {exc}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                },
            )
            raise
