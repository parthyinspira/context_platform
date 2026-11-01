import os
from typing import Any

import psycopg


def get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set")
    return database_url


def get_connection_factory() -> Any:
    """Return a zero-arg callable that opens a fresh connection per call."""
    database_url = get_database_url()
    return lambda: psycopg.connect(database_url)
