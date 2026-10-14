from pathlib import Path

from sqlalchemy import Engine, create_engine, make_url
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def open_database(database_url: str) -> Engine:
    """Open the database, creating its folder and tables if they are missing."""
    # Import the table definitions so create_all knows about them.
    from server.store import artifacts, chats  # noqa: F401

    path = make_url(database_url).database
    if path and path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine
