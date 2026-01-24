"""Database engine initialization.

This module creates and configures the SQLAlchemy engine for the ECHO database.
The database configuration is loaded from settings/environment variables.
"""

import os
from pathlib import Path

from sqlalchemy import URL, Engine, create_engine

from core.logger import get_logger
from core.settings import get_settings

logger = get_logger(__name__)

# Load settings
settings = get_settings()


def make_engine(db_url: str | URL, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine with the given database URL.

    Args:
        db_url: Database connection URL
        echo: Enable SQL query logging

    Returns:
        Engine: Configured SQLAlchemy engine
    """
    return create_engine(db_url, echo=echo)


def _ensure_database_directory() -> None:
    """Ensure the database directory exists for SQLite databases.

    For SQLite databases, creates the parent directory if it doesn't exist.
    For other database types, this is a no-op.
    """
    db_path = settings.database.path
    if db_path:
        # SQLite database - ensure directory exists
        db_dir = db_path.parent
        if not db_dir.exists():
            logger.info(
                f"Creating database directory: {db_dir}",
                extra={"db_directory": str(db_dir)},
            )
            os.makedirs(db_dir, exist_ok=True)
        else:
            logger.debug(
                f"Database directory exists: {db_dir}",
                extra={"db_directory": str(db_dir)},
            )


# Initialize database engine
logger.info(
    "Initializing database engine",
    extra={"database_url": settings.database.url.split("://")[0] + "://..."},
)

# Ensure directory exists for SQLite
_ensure_database_directory()

# Create engine
echo_engine = make_engine(settings.database.url, echo=False)

logger.info(
    "Database engine initialized successfully",
    extra={
        "database_type": settings.database.url.split(":")[0],
        "database_path": str(settings.database.path) if settings.database.path else "N/A",
    },
)
