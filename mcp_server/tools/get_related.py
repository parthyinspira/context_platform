"""get_related: depth-limited edge traversal via recursive CTE (KAN-33).

Returns entities reachable from a starting entity within `depth` hops,
each with the connecting relation and a citation (source_link, harvested_at,
sensitivity, confidence).  Tombstoned entities are excluded at the DB level.
"""
from __future__ import annotations

from typing import Any


_CTE_SQL = """
WITH RECURSIVE traverse(entity_id, relation, confidence, source_id, depth) AS (
    -- Seed: direct neighbours of the start entity
    SELECT
        CASE WHEN src_entity_id = %(start)s THEN dst_entity_id ELSE src_entity_id END,
        relation,
        confidence,
        source_id,
        1
    FROM edges
    WHERE (
        (%(direction)s IN ('out', 'both') AND src_entity_id = %(start)s)
        OR (%(direction)s IN ('in', 'both') AND dst_entity_id = %(start)s)
    )
    AND (%(relation_filter)s IS NULL OR relation = %(relation_filter)s)

    UNION

    -- Recursive: extend from the current frontier
    SELECT
        CASE WHEN e.src_entity_id = t.entity_id THEN e.dst_entity_id ELSE e.src_entity_id END,
        e.relation,
        e.confidence,
        e.source_id,
        t.depth + 1
    FROM edges e
    JOIN traverse t ON (
        (%(direction)s IN ('out', 'both') AND e.src_entity_id = t.entity_id)
        OR (%(direction)s IN ('in', 'both') AND e.dst_entity_id = t.entity_id)
    )
    WHERE t.depth < %(depth)s
    AND (%(relation_filter)s IS NULL OR e.relation = %(relation_filter)s)
)
SELECT DISTINCT ON (ent.id)
    ent.id,
    ent.type,
    ent.name,
    ent.source_id,
    t.relation,
    t.confidence,
    s.uri          AS source_link,
    s.sensitivity,
    s.last_harvest_at
FROM traverse t
JOIN entities ent ON ent.id = t.entity_id AND ent.tombstoned_at IS NULL
JOIN sources s ON s.id = ent.source_id
WHERE ent.id != %(start)s
ORDER BY ent.id, t.depth
"""

def get_related(
    conn: Any,
    *,
    entity_id: str,
    relation: str | None = None,
    depth: int = 3,
    direction: str = "both",
) -> list[dict[str, Any]]:
    """Traverse edges from *entity_id* up to *depth* hops.

    Parameters
    ----------
    conn:
        A DB connection object with a ``cursor()`` method (psycopg or fake).
    entity_id:
        UUID of the starting entity.
    relation:
        If given, only edges with this relation label are followed.
    depth:
        Maximum number of hops (default 3, max enforced by caller).
    direction:
        ``"out"`` (outbound only), ``"in"`` (inbound only), or ``"both"``.

    Returns
    -------
    list of dicts with keys: entity_id, type, name, source_id, relation,
    confidence, source_link, harvested_at, sensitivity.
    """
    if direction not in ("out", "in", "both"):
        raise ValueError(f"direction must be 'out', 'in' or 'both', got {direction!r}")
    if depth < 1:
        raise ValueError(f"depth must be >= 1, got {depth}")

    cur = conn.cursor()
    cur.execute(
        _CTE_SQL,
        {
            "start": entity_id,
            "direction": direction,
            "relation_filter": relation,
            "depth": depth,
        },
    )
    rows = cur.fetchall()

    return [
        {
            "entity_id": str(row[0]),
            "type": row[1],
            "name": row[2],
            "source_id": str(row[3]),
            "relation": row[4],
            "confidence": float(row[5]),
            "source_link": row[6],
            "sensitivity": row[7],
            "harvested_at": str(row[8]) if row[8] is not None else None,
        }
        for row in rows
    ]
