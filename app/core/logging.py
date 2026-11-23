"""Structured JSON Logging Module.

Provides standard JSON-formatted log lines with timestamp, level,
module, trace ID, request ID, and contextual attributes for production observability.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Custom logging formatter that outputs JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include contextual attributes if present in record.__dict__
        for attr in ("request_id", "trace_id", "tenant_id", "document_id", "duration_ms"):
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(debug: bool = False) -> None:
    """Initialize structured logging configuration for the entire application."""
    log_level = logging.DEBUG if debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on re-initialization
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

    # Silence chatty third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured for the specified module name."""
    return logging.getLogger(name)
