"module"

import os
from pathlib import Path

from sqlalchemy import URL, Engine, create_engine


def make_engine(db_url: str | URL, echo: bool = False) -> Engine:
    "function"
    # Create an SQLite engine (creates the file if it doesn't exist)
    return create_engine(db_url, echo=echo)  # echo=True for SQL logging (optional)


# TODO: Refactor to use config management
# Get the absolute path to the data directory
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "src" / "data"
os.makedirs(data_dir, exist_ok=True)
db_path = data_dir / "echo.db"

echo_engine = make_engine(f"sqlite:///{db_path}", echo=False)
