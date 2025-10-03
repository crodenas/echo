"module"

from sqlalchemy import URL, Engine, create_engine


def make_engine(db_url: str | URL, echo: bool = False) -> Engine:
    "function"
    # Create an SQLite engine (creates the file if it doesn't exist)
    return create_engine(db_url, echo=echo)  # echo=True for SQL logging (optional)


echo_engine = make_engine("sqlite:///data/echo.db", echo=True)
