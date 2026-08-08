"""Structured Logging Configuration Module.

Provides a unified logger configuration with formatted output for tracking
asynchronous operations, crawling lifecycle events, and exceptions.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from src.core.config import settings


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for production log collectors."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging() -> logging.Logger:
    """Configures system-wide structured logging.

    Returns:
        logging.Logger: Configured root application logger instance.
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    if getattr(settings, "LOG_FORMAT", "json").lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    logger = logging.getLogger("web_scraper")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        logger.addHandler(console_handler)

    # Suppress verbose noisy third-party logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    return logger


logger = setup_logging()
