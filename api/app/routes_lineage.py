"""Lineage traversal endpoint (KAN-48).

GET /lineage/{entity_id}?direction=downstream&depth=5

Uses a recursive CTE to traverse READS_FROM, WRITES_TO and DERIVED_FROM edges
up to the requested depth. Tombstoned entities are excluded. Each node in the
response carries source_link, harvested_at (from most-recent chunk) and
sensitivity as citations.

Direction semantics:
  downstream — entities that consume or are produced from the start entity
    • X --READS_FROM--> start  (X reads from start)
    • start --WRITES_TO--> X   (start produces X)
    • X --DERIVED_FROM--> start (X is derived from start)
  upstream — entities that the start entity depends on or is produced by
    • start --READS_FROM--> X  (start reads from X)
    • X --WRITES_TO--> start   (X produces start)
    • start --DERIVED_FROM--> X (start is derived from X)
"""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException

from app.main import connection_factory_dependency
from app.schemas_lineage import LineageEdgeOut, LineageNodeOut, LineageOut

router = APIRouter()

_LINEAGE_RELATIONS = ("READS_FROM", "WRITES_TO", "DERIVED_FROM")

# Downstream: next node is dst for WRITES_TO, src otherwise.
_DOWNSTREAM_CTE = """
WITH RECURSIVE lineage(
    next_id, edge_id, src_entity_id, dst_entity_id, relation, confidence,
    edge_source_id, depth, visited
) AS (
    SELECT
        CASE WHEN e.relation = 'WRITES_TO' THEN e.dst_entity_id ELSE e.src_entity_id END,
        e.id, e.src_entity_id, e.dst_entity_id, e.relation, e.confidence, e.source_id,
        1, ARRAY[%(start_id)s::uuid]
    FROM edges e
    WHERE (
        (e.relation IN ('READS_FROM', 'DERIVED_FROM') AND e.dst_entity_id = %(start_id)s)
        OR (e.relation = 'WRITES_TO' AND e.src_entity_id = %(start_id)s)
    )
    AND e.relation IN ('READS_FROM', 'WRITES_TO', 'DERIVED_FROM')

    UNION ALL

    SELECT
        CASE WHEN e.relation = 'WRITES_TO' THEN e.dst_entity_id ELSE e.src_entity_id END,
        e.id, e.src_entity_id, e.dst_entity_id, e.relation, e.confidence, e.source_id,
        l.depth + 1, l.visited || l.next_id
    FROM edges e
    JOIN lineage l ON (
        (e.relation IN ('READS_FROM', 'DERIVED_FROM') AND e.dst_entity_id = l.next_id)
        OR (e.relation = 'WRITES_TO' AND e.src_entity_id = l.next_id)
    )
    WHERE l.depth < %(max_depth)s
    AND e.relation IN ('READS_FROM', 'WRITES_TO', 'DERIVED_FROM')
    AND NOT (l.next_id = ANY(l.visited))
)
SELECT DISTINCT ON (ent.id)
    ent.id, ent.type, ent.name, ent.source_id, ent.props,
    l.edge_id, l.src_entity_id, l.dst_entity_id, l.relation, l.confidence,
    l.depth,
    src.uri, src.sensitivity,
    ch.harvested_at
FROM lineage l
JOIN entities ent ON ent.id = l.next_id AND ent.tombstoned_at IS NULL
JOIN sources src ON src.id = ent.source_id
LEFT JOIN LATERAL (
    SELECT harvested_at FROM chunks WHERE entity_id = ent.id ORDER BY harvested_at DESC LIMIT 1
) ch ON TRUE
ORDER BY ent.id, l.depth
"""

# Upstream: next node is src for WRITES_TO, dst otherwise.
_UPSTREAM_CTE = """
WITH RECURSIVE lineage(
    next_id, edge_id, src_entity_id, dst_entity_id, relation, confidence,
    edge_source_id, depth, visited
) AS (
    SELECT
        CASE WHEN e.relation = 'WRITES_TO' THEN e.src_entity_id ELSE e.dst_entity_id END,
        e.id, e.src_entity_id, e.dst_entity_id, e.relation, e.confidence, e.source_id,
        1, ARRAY[%(start_id)s::uuid]
    FROM edges e
    WHERE (
        (e.relation IN ('READS_FROM', 'DERIVED_FROM') AND e.src_entity_id = %(start_id)s)
        OR (e.relation = 'WRITES_TO' AND e.dst_entity_id = %(start_id)s)
    )
    AND e.relation IN ('READS_FROM', 'WRITES_TO', 'DERIVED_FROM')

    UNION ALL

    SELECT
        CASE WHEN e.relation = 'WRITES_TO' THEN e.src_entity_id ELSE e.dst_entity_id END,
        e.id, e.src_entity_id, e.dst_entity_id, e.relation, e.confidence, e.source_id,
        l.depth + 1, l.visited || l.next_id
    FROM edges e
    JOIN lineage l ON (
        (e.relation IN ('READS_FROM', 'DERIVED_FROM') AND e.src_entity_id = l.next_id)
        OR (e.relation = 'WRITES_TO' AND e.dst_entity_id = l.next_id)
    )
    WHERE l.depth < %(max_depth)s
    AND e.relation IN ('READS_FROM', 'WRITES_TO', 'DERIVED_FROM')
    AND NOT (l.next_id = ANY(l.visited))
)
SELECT DISTINCT ON (ent.id)
    ent.id, ent.type, ent.name, ent.source_id, ent.props,
    l.edge_id, l.src_entity_id, l.dst_entity_id, l.relation, l.confidence,
    l.depth,
    src.uri, src.sensitivity,
    ch.harvested_at
FROM lineage l
JOIN entities ent ON ent.id = l.next_id AND ent.tombstoned_at IS NULL
JOIN sources src ON src.id = ent.source_id
LEFT JOIN LATERAL (
    SELECT harvested_at FROM chunks WHERE entity_id = ent.id ORDER BY harvested_at DESC LIMIT 1
) ch ON TRUE
ORDER BY ent.id, l.depth
"""


@router.get("/lineage/{entity_id}", response_model=LineageOut)
def get_lineage(
    entity_id: str,
    direction: Literal["downstream", "upstream"] = "downstream",
    depth: int = 5,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> LineageOut:
    if depth < 1 or depth > 10:
        raise HTTPException(status_code=422, detail="depth must be between 1 and 10")

    conn = connection_factory()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM entities WHERE id = %s AND tombstoned_at IS NULL",
            (entity_id,),
        )
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="entity not found")

        cte = _DOWNSTREAM_CTE if direction == "downstream" else _UPSTREAM_CTE
        cur.execute(cte, {"start_id": entity_id, "max_depth": depth})
        rows = cur.fetchall()
    finally:
        conn.close()

    seen_nodes: dict[str, LineageNodeOut] = {}
    seen_edges: dict[str, LineageEdgeOut] = {}

    for row in rows:
        (
            ent_id, ent_type, name, source_id, props,
            edge_id, src_entity_id, dst_entity_id, relation, confidence,
            row_depth,
            source_uri, sensitivity,
            harvested_at,
        ) = row

        if ent_id not in seen_nodes:
            seen_nodes[ent_id] = LineageNodeOut(
                id=str(ent_id),
                type=ent_type,
                name=name,
                source_id=str(source_id),
                props=props or {},
                depth=row_depth,
                source_link=source_uri,
                harvested_at=str(harvested_at) if harvested_at else None,
                sensitivity=sensitivity,
            )

        if edge_id not in seen_edges:
            seen_edges[edge_id] = LineageEdgeOut(
                id=str(edge_id),
                src_entity_id=str(src_entity_id),
                dst_entity_id=str(dst_entity_id),
                relation=relation,
                confidence=float(confidence),
            )

    return LineageOut(
        start_entity_id=entity_id,
        direction=direction,
        depth=depth,
        nodes=list(seen_nodes.values()),
        edges=list(seen_edges.values()),
    )
