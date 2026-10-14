import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings, read from environment variables so nothing is hard-coded."""

    database_url: str


def load_settings() -> Settings:
    return Settings(database_url=os.environ.get("MTM_DATABASE_URL", "sqlite:///data/app.db"))
