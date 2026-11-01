from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.main import connection_factory_dependency
from app.schemas import EntityResult, RelatedResult

router = APIRouter()


@router.get("/entities/{entity_id}", response_model=EntityResult)
def get_entity(
    entity_id: str,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> EntityResult:
    conn = connection_factory()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT e.id, e.type, e.name, e.props, s.uri, s.sensitivity "
            "FROM entities e JOIN sources s ON s.id = e.source_id "
            "WHERE e.id = %s AND e.tombstoned_at IS NULL",
            (entity_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="entity not found")
        eid, etype, ename, props, source_link, sensitivity = row

        cur.execute(
            "SELECT MIN(harvested_at) FROM chunks WHERE entity_id = %s",
            (entity_id,),
        )
        ha_row = cur.fetchone()
        if ha_row and ha_row[0]:
            harvested_at: str | None = (
                ha_row[0].isoformat() if hasattr(ha_row[0], "isoformat") else str(ha_row[0])
            )
        else:
            harvested_at = None

        cur.execute(
            "SELECT eg.src_entity_id, eg.dst_entity_id, eg.relation, en.type, en.name "
            "FROM edges eg "
            "JOIN entities en ON en.id = CASE "
            "  WHEN eg.src_entity_id = %s THEN eg.dst_entity_id "
            "  ELSE eg.src_entity_id END "
            "AND en.tombstoned_at IS NULL "
            "WHERE (eg.src_entity_id = %s OR eg.dst_entity_id = %s)",
            (entity_id, entity_id, entity_id),
        )
        related = []
        for src, dst, relation, ntype, nname in cur.fetchall():
            neighbor_id = dst if src == entity_id else src
            rel_direction = "out" if src == entity_id else "in"
            related.append(
                RelatedResult(
                    entity_id=str(neighbor_id),
                    entity_type=ntype,
                    entity_name=nname,
                    relation=relation,
                    direction=rel_direction,
                )
            )
    finally:
        conn.close()

    return EntityResult(
        entity_id=str(eid),
        entity_type=etype,
        entity_name=ename,
        props=props or {},
        source_link=source_link,
        sensitivity=sensitivity,
        harvested_at=harvested_at,
        related=related,
    )


@router.get("/entities/{entity_id}/related", response_model=list[RelatedResult])
def get_related(
    entity_id: str,
    relation: str | None = None,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> list[RelatedResult]:
    conn = connection_factory()
    try:
        cur = conn.cursor()
        sql = (
            "SELECT eg.src_entity_id, eg.dst_entity_id, eg.relation, en.type, en.name "
            "FROM edges eg "
            "JOIN entities en ON en.id = CASE "
            "  WHEN eg.src_entity_id = %s THEN eg.dst_entity_id "
            "  ELSE eg.src_entity_id END "
            "AND en.tombstoned_at IS NULL "
            "WHERE (eg.src_entity_id = %s OR eg.dst_entity_id = %s)"
        )
        params: list[Any] = [entity_id, entity_id, entity_id]
        if relation:
            sql += " AND eg.relation = %s"
            params.append(relation)
        cur.execute(sql, params)
        results = []
        for src, dst, rel, ntype, nname in cur.fetchall():
            neighbor_id = dst if src == entity_id else src
            rel_direction = "out" if src == entity_id else "in"
            results.append(
                RelatedResult(
                    entity_id=str(neighbor_id),
                    entity_type=ntype,
                    entity_name=nname,
                    relation=rel,
                    direction=rel_direction,
                )
            )
    finally:
        conn.close()
    return results
