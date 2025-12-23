"""
Application logger configuration.

Usage:
    from core.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Hello, world!")
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger for the application.

    Uses logging.basicConfig which is a no-op if handlers are already configured
    (e.g., by uvicorn), preventing duplicate log output.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: The name of the module, typically __name__.

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)
