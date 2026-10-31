#!/usr/bin/env python3
"""Apply or roll back the SQL migrations under migrations/.

Usage:
    python scripts/migrate.py up [DATABASE_URL]
    python scripts/migrate.py down [DATABASE_URL]

DATABASE_URL defaults to the DATABASE_URL environment variable.
"""
import os
import sys
from pathlib import Path

import psycopg

def _migrations_dir() -> Path:
    script_dir = Path(__file__).resolve().parent
    for candidate in (script_dir / "migrations", script_dir.parent / "migrations"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"no migrations directory found next to or above {script_dir}")


MIGRATIONS_DIR = _migrations_dir()


def _migration_versions() -> list[str]:
    return sorted({p.name.split(".", 1)[0] for p in MIGRATIONS_DIR.glob("*.up.sql")})


def apply_migrations(database_url: str) -> None:
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}

        for version in _migration_versions():
            if version in applied:
                continue
            sql_path = MIGRATIONS_DIR / f"{version}.up.sql"
            with conn.transaction():
                conn.execute(sql_path.read_text())
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)", (version,)
                )


def rollback_migrations(database_url: str) -> None:
    with psycopg.connect(database_url, autocommit=True) as conn:
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}

        for version in sorted(applied, reverse=True):
            sql_path = MIGRATIONS_DIR / f"{version}.down.sql"
            with conn.transaction():
                conn.execute(sql_path.read_text())
                conn.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("up", "down"):
        print(__doc__)
        return 2
    direction = sys.argv[1]
    database_url = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL must be set or passed as an argument")
        return 2

    if direction == "up":
        apply_migrations(database_url)
    else:
        rollback_migrations(database_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
