"""Structured Logging Configuration Module.

Provides a unified logger configuration with formatted output for tracking
asynchronous operations, crawling lifecycle events, and exceptions.
"""

import logging
import sys
from src.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures system-wide structured logging.

    Returns:
        logging.Logger: Configured root application logger instance.
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Custom log format with timestamp, log level, module name, and message
    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
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
