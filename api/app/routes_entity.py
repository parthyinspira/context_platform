"""Entity detail route (KAN-68): properties, edges grouped by relation, citations
(source link, harvested_at, run id), owner and the source uri for "open in source".
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.main import connection_factory_dependency
from app.schemas_entity import CitationOut, EdgeNeighborOut, EntityOut

router = APIRouter()


@router.get("/entities/{entity_id}", response_model=EntityOut)
def get_entity(
    entity_id: str,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> EntityOut:
    conn = connection_factory()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT id, type, name, source_id, props FROM entities WHERE id = %s "
            "AND tombstoned_at IS NULL",
            (entity_id,),
        )
        entity_row = cur.fetchone()
        if entity_row is None:
            raise HTTPException(status_code=404, detail="entity not found")
        _, entity_type, name, source_id, props = entity_row

        cur.execute(
            "SELECT id, uri, owner FROM sources WHERE id = %s",
            (source_id,),
        )
        source_row = cur.fetchone()
        _, source_uri, owner = source_row

        cur.execute(
            "SELECT id, src_entity_id, dst_entity_id, relation FROM edges "
            "WHERE src_entity_id = %s OR dst_entity_id = %s",
            (entity_id, entity_id),
        )
        edge_rows = cur.fetchall()

        neighbor_ids = {
            (dst if src == entity_id else src) for _, src, dst, _ in edge_rows
        }
        neighbors: dict[str, tuple[str, str]] = {}
        if neighbor_ids:
            cur.execute(
                "SELECT id, type, name FROM entities WHERE id = ANY(%s) "
                "AND tombstoned_at IS NULL",
                (list(neighbor_ids),),
            )
            neighbors = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

        edges_by_relation: dict[str, list[EdgeNeighborOut]] = defaultdict(list)
        for edge_id, src, dst, relation in edge_rows:
            neighbor_id = dst if src == entity_id else src
            neighbor = neighbors.get(neighbor_id)
            if neighbor is None:
                continue  # neighbour is tombstoned or missing
            direction = "out" if src == entity_id else "in"
            edges_by_relation[relation].append(
                EdgeNeighborOut(
                    id=edge_id,
                    direction=direction,
                    entity_id=neighbor_id,
                    entity_type=neighbor[0],
                    entity_name=neighbor[1],
                )
            )

        cur.execute(
            "SELECT id, harvested_at FROM chunks WHERE entity_id = %s",
            (entity_id,),
        )
        chunk_rows = cur.fetchall()

        cur.execute(
            "SELECT id, started_at FROM harvest_runs WHERE source_id = %s "
            "ORDER BY started_at DESC",
            (source_id,),
        )
        runs = cur.fetchall()  # already most-recent-first

        citations = [
            CitationOut(
                source_link=source_uri,
                harvested_at=harvested_at,
                run_id=_latest_run_at_or_before(runs, harvested_at),
            )
            for _, harvested_at in chunk_rows
        ]
    finally:
        conn.close()

    return EntityOut(
        id=entity_id,
        type=entity_type,
        name=name,
        props=props or {},
        owner=owner,
        source_uri=source_uri,
        edges_by_relation=dict(edges_by_relation),
        citations=citations,
    )


def _latest_run_at_or_before(runs: list[tuple[str, str]], harvested_at: str) -> str | None:
    """`runs` is sorted most-recent-first; find the first one at or before
    `harvested_at` (string timestamps compare correctly as ISO 8601 UTC).
    """
    for run_id, started_at in runs:
        if started_at <= harvested_at:
            return run_id
    return None
