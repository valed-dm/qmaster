"""
Logging configuration for the application.

Uses Loguru for structured logging with file rotation and contextual binding.
"""

from loguru import logger

from .config import settings


log = logger.bind(name="QMASTER")

log.add(
    settings.LOG_FILE,
    format="{time} {level} [{extra[name]}] {message}",
    rotation="500 KB",
    backtrace=True,
    diagnose=True,
    level="DEBUG",
    enqueue=True,
)
