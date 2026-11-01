"""search_context query logic — runs against the Postgres store."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    text: str
    source_link: str
    harvested_at: str  # ISO-8601 string
    sensitivity: str


def search_context(conn: Any, query: str, limit: int = 5) -> list[SearchResult]:
    """Return up to *limit* chunks matching *query* (case-insensitive substring).

    Excludes chunks whose entity is tombstoned.
    Each result carries the source URI, harvested_at timestamp and sensitivity.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                c.text,
                s.uri        AS source_link,
                c.harvested_at,
                s.sensitivity
            FROM chunks c
            JOIN sources s ON s.id = c.source_id
            LEFT JOIN entities e ON e.id = c.entity_id
            WHERE
                c.text ILIKE %s
                AND (e.id IS NULL OR e.tombstoned_at IS NULL)
            ORDER BY c.harvested_at DESC
            LIMIT %s
            """,
            (f"%{query}%", limit),
        )
        rows = cur.fetchall()

    return [
        SearchResult(
            text=row[0],
            source_link=row[1],
            harvested_at=row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
            sensitivity=row[3],
        )
        for row in rows
    ]
