"""Logging configuration for License Server using Loguru."""
import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings


def setup_logging():
    """Setup application logging with Loguru."""
    # Remove default handler
    logger.remove()

    # Create logs directory
    log_file = Path(settings.logging.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Parse log level
    level = settings.logging.level.upper()

    # Console handler with colors and formatted output
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
    )

    # File handler with rotation
    logger.add(
        settings.logging.file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=level,
        rotation=settings.logging.max_bytes,  # Rotate when file reaches max bytes
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress rotated logs
        enqueue=True,  # Async logging
        backtrace=True,  # Full stack trace on errors
        diagnose=True,  # Show variable values on errors
    )

    # Intercept standard logging messages and redirect to loguru
    import logging

    class InterceptHandler(logging.Handler):
        """Intercept standard logging and redirect to loguru."""

        def emit(self, record):
            """Emit a log record to loguru."""
            # Get corresponding loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    # Intercept all standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logger.info(f"Logging configured: {level}")


# Export logger for use in other modules
__all__ = ["logger"]
