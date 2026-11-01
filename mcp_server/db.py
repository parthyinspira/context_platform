"""Postgres connection factory for the MCP server (same pattern as api/app/db.py)."""
import os
from typing import Any

import psycopg


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be set")
    return url


def get_connection_factory() -> "Any":
    url = get_database_url()
    return lambda: psycopg.connect(url)
