"""Structured JSON Logging System for DealGuard AI."""

import logging
import sys
from typing import Any, Dict

try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:
    from pythonjsonlogger.jsonlogger import JsonFormatter  # type: ignore

from app.core.config import settings



class CustomJsonFormatter(JsonFormatter):

    """Custom JSON formatter adding service metadata and timestamp format."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["service"] = "dealguard-backend"
        log_record["environment"] = settings.ENVIRONMENT
        log_record["level"] = record.levelname
        log_record["logger_name"] = record.name
        if "timestamp" not in log_record:
            log_record["timestamp"] = self.formatTime(record, self.datefmt)


def setup_logging() -> None:
    """Configure root logger with structured JSON output."""
    root_logger = logging.getLogger()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicate logs
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if settings.ENVIRONMENT == "development" and settings.DEBUG:
        # Human-readable format for local development
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Production structured JSON
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(service)s %(environment)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)
