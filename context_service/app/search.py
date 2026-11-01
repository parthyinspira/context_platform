"""Hybrid search: combines keyword (tsvector) and vector (pgvector cosine) scores via RRF."""
from __future__ import annotations

from typing import Any

_LINEAGE_RELATIONS = {"READS_FROM", "WRITES_TO", "DERIVED_FROM"}


def hybrid_search(
    conn: Any,
    q: str,
    *,
    source_ids: list[str] | None = None,
    entity_types: list[str] | None = None,
    sensitivities: list[str] | None = None,
    limit: int = 20,
) -> list[dict]:
    """Reciprocal Rank Fusion over keyword + vector ranked lists."""
    cur = conn.cursor()

    sens_clause = ""
    sens_params: list[Any] = []
    if sensitivities is not None:
        sens_clause = "AND s.sensitivity = ANY(%s)"
        sens_params.append(sensitivities)

    source_clause = ""
    source_params: list[Any] = []
    if source_ids is not None:
        source_clause = "AND c.source_id = ANY(%s)"
        source_params.append(source_ids)

    type_clause = ""
    type_params: list[Any] = []
    if entity_types is not None:
        type_clause = "AND e.type = ANY(%s)"
        type_params.append(entity_types)

    common_joins = """
        FROM chunks c
        JOIN entities e ON e.id = c.entity_id AND e.tombstoned_at IS NULL
        JOIN sources s ON s.id = c.source_id
    """
    common_where = f"WHERE 1=1 {sens_clause} {source_clause} {type_clause}"
    common_params = sens_params + source_params + type_params

    kw_sql = f"""
        SELECT c.id AS chunk_id,
               ROW_NUMBER() OVER (
                   ORDER BY ts_rank(to_tsvector('english', c.text), plainto_tsquery('english', %s)) DESC
               ) AS rk
        {common_joins}
        {common_where}
        AND to_tsvector('english', c.text) @@ plainto_tsquery('english', %s)
        ORDER BY rk
        LIMIT %s
    """
    kw_params = [q] + common_params + [q, limit * 5]
    cur.execute(kw_sql, kw_params)
    kw_ranks = {row[0]: row[1] for row in cur.fetchall()}

    vec_ranks: dict[str, int] = {}
    try:
        # Proxy-embedding: use the top keyword result's stored vector as the query vector.
        # This avoids a round-trip to an embedding service in this story. Replace with a
        # proper query embedding call (EmbeddingProvider.embed(q)) once KAN-32+ wires it up.
        if kw_ranks:
            top_chunk_id = min(kw_ranks, key=lambda k: kw_ranks[k])
            cur.execute("SELECT embedding FROM chunks WHERE id = %s", (top_chunk_id,))
            emb_row = cur.fetchone()
            if emb_row and emb_row[0] is not None:
                query_vec = emb_row[0]
                vec_sql = f"""
                    SELECT c.id AS chunk_id,
                           ROW_NUMBER() OVER (ORDER BY c.embedding <=> %s::vector) AS rk
                    {common_joins}
                    {common_where}
                    AND c.embedding IS NOT NULL
                    ORDER BY rk
                    LIMIT %s
                """
                vec_params = [query_vec] + common_params + [limit * 5]
                cur.execute(vec_sql, vec_params)
                vec_ranks = {row[0]: row[1] for row in cur.fetchall()}
    except Exception:
        pass  # vector search unavailable; fall back to keyword only

    k = 60
    all_chunks = set(kw_ranks) | set(vec_ranks)
    rrf_scores = {
        cid: (
            1.0 / (k + kw_ranks.get(cid, limit * 5 + 1))
            + 1.0 / (k + vec_ranks.get(cid, limit * 5 + 1))
        )
        for cid in all_chunks
    }
    top_chunks = sorted(rrf_scores, key=lambda c: rrf_scores[c], reverse=True)[:limit]

    if not top_chunks:
        return []

    cur.execute(
        """
        SELECT c.id, c.text, c.harvested_at, e.id, e.type, e.name, s.uri, s.sensitivity
        FROM chunks c
        JOIN entities e ON e.id = c.entity_id AND e.tombstoned_at IS NULL
        JOIN sources s ON s.id = c.source_id
        WHERE c.id = ANY(%s)
        """,
        (top_chunks,),
    )
    rows = cur.fetchall()
    row_map = {r[0]: r for r in rows}

    results = []
    for cid in top_chunks:
        if cid not in row_map:
            continue
        r = row_map[cid]
        results.append(
            {
                "chunk_id": str(r[0]),
                "text": r[1],
                "harvested_at": r[2].isoformat() if hasattr(r[2], "isoformat") else str(r[2]),
                "entity_id": str(r[3]),
                "entity_type": r[4],
                "entity_name": r[5],
                "source_link": r[6],
                "sensitivity": r[7],
                "score": rrf_scores.get(cid, 0.0),
            }
        )
    return results


def get_lineage(
    conn: Any,
    entity_id: str,
    direction: str,
    max_depth: int,
) -> tuple[list[dict], list[dict]]:
    """BFS traversal of READS_FROM/WRITES_TO/DERIVED_FROM edges."""
    cur = conn.cursor()
    visited: set[str] = {entity_id}
    queue = [(entity_id, 0)]
    nodes: list[dict] = []
    edges: list[dict] = []

    cur.execute(
        "SELECT id, type, name FROM entities WHERE id = %s AND tombstoned_at IS NULL",
        (entity_id,),
    )
    root = cur.fetchone()
    if root:
        nodes.append(
            {"entity_id": str(root[0]), "entity_type": root[1], "entity_name": root[2], "depth": 0}
        )

    while queue:
        current_id, depth = queue.pop(0)
        if depth >= max_depth:
            continue

        if direction in ("downstream", "both"):
            cur.execute(
                "SELECT id, src_entity_id, dst_entity_id, relation, confidence FROM edges "
                "WHERE src_entity_id = %s AND relation = ANY(%s)",
                (current_id, list(_LINEAGE_RELATIONS)),
            )
            for _eid, src, dst, rel, conf in cur.fetchall():
                if dst not in visited:
                    visited.add(dst)
                    cur.execute(
                        "SELECT id, type, name FROM entities WHERE id = %s AND tombstoned_at IS NULL",
                        (dst,),
                    )
                    row = cur.fetchone()
                    if row:
                        nodes.append(
                            {
                                "entity_id": str(row[0]),
                                "entity_type": row[1],
                                "entity_name": row[2],
                                "depth": depth + 1,
                            }
                        )
                        queue.append((dst, depth + 1))
                edges.append(
                    {"src_entity_id": src, "dst_entity_id": dst, "relation": rel, "confidence": conf}
                )

        if direction in ("upstream", "both"):
            cur.execute(
                "SELECT id, src_entity_id, dst_entity_id, relation, confidence FROM edges "
                "WHERE dst_entity_id = %s AND relation = ANY(%s)",
                (current_id, list(_LINEAGE_RELATIONS)),
            )
            for _eid, src, dst, rel, conf in cur.fetchall():
                if src not in visited:
                    visited.add(src)
                    cur.execute(
                        "SELECT id, type, name FROM entities WHERE id = %s AND tombstoned_at IS NULL",
                        (src,),
                    )
                    row = cur.fetchone()
                    if row:
                        nodes.append(
                            {
                                "entity_id": str(row[0]),
                                "entity_type": row[1],
                                "entity_name": row[2],
                                "depth": depth + 1,
                            }
                        )
                        queue.append((src, depth + 1))
                edges.append(
                    {"src_entity_id": src, "dst_entity_id": dst, "relation": rel, "confidence": conf}
                )

    return nodes, edges
