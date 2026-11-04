"""POST /ontology/extract — cross-source ontology extraction.

Two-tier pipeline:
  Tier 1 (normalize): entity-per-file within one source  ← already done
  Tier 2 (this):      read file content, detect cross-source relationships,
                      write READS_FROM / WRITES_TO / DEPENDS_ON / DERIVED_FROM edges

Extraction strategy
-------------------
1. Load every entity from the DB with its source URI (stored in props.uri).
2. For each file entity whose URI resolves to a GitHub blob URL, fetch the
   raw content (rate-limit friendly: skip binary / large files).
3. Parse content by entity type:
     Table/SQL  → sqlglot AST → extract referenced table names
     Module/Py  → regex import analysis → extract imported module names
     Document   → keyword scan for entity names
4. For every extracted name, fuzzy-match against all known entity names across
   ALL sources.  When a match is found, write the appropriate directed edge.
5. Additional heuristics for common patterns:
     *_loader.*, *_etl.*, *_pipeline.*  → WRITES_TO same-named Table entities
     report_*.*, *.dax, *.pbix          → READS_FROM Table entities with matching names
     *_test.*, test_*.*                 → DEPENDS_ON the module under test

All writes are idempotent (ON CONFLICT DO NOTHING).
"""
from __future__ import annotations

import json
import logging
import re
import urllib.request
from pathlib import PurePosixPath
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.main import connection_factory_dependency

logger = logging.getLogger(__name__)
router = APIRouter()


# ── GitHub content fetch ──────────────────────────────────────────────────────

def _raw_url(blob_url: str) -> str | None:
    """Convert https://github.com/owner/repo/blob/BRANCH/path  →  raw URL."""
    if "github.com" not in blob_url:
        return None
    url = blob_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url


def _fetch(url: str, max_bytes: int = 80_000, timeout: int = 8) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "context-platform-ontology/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(max_bytes).decode("utf-8", errors="ignore")
    except Exception as exc:
        logger.debug("fetch failed %s: %s", url, exc)
        return None


# ── SQL analysis ──────────────────────────────────────────────────────────────

def _sql_refs(content: str) -> tuple[list[str], list[str]]:
    """Return (reads, writes) table names.  Uses sqlglot when available."""
    reads: list[str] = []
    writes: list[str] = []
    try:
        import sqlglot
        import sqlglot.expressions as exp
        for stmt in sqlglot.parse(content, error_level=sqlglot.ErrorLevel.IGNORE):
            if stmt is None:
                continue
            # tables in FROM / JOIN
            for t in stmt.find_all(exp.Table):
                if t.name:
                    reads.append(t.name.lower())
            # INSERT / MERGE / UPDATE targets
            for cls in (exp.Insert, exp.Update, exp.Create):
                node = stmt.find(cls)
                if node:
                    tbl = node.find(exp.Table)
                    if tbl and tbl.name:
                        writes.append(tbl.name.lower())
                        # remove from reads (it's a write target)
                        reads = [r for r in reads if r != tbl.name.lower()]
    except Exception:
        # Fallback: regex
        for m in re.finditer(r'\b(?:FROM|JOIN)\s+([\w]+)', content, re.IGNORECASE):
            n = m.group(1).lower()
            if n not in {"select", "where", "on", "and", "or", "null", "as", "lateral", "unnest"}:
                reads.append(n)
        for m in re.finditer(r'\b(?:INSERT\s+INTO|MERGE\s+INTO|UPDATE|CREATE\s+(?:OR\s+REPLACE\s+)?TABLE)\s+([\w]+)', content, re.IGNORECASE):
            writes.append(m.group(1).lower())
            reads = [r for r in reads if r != m.group(1).lower()]
    return list(set(reads)), list(set(writes))


# ── Python import analysis ────────────────────────────────────────────────────

def _py_imports(content: str) -> list[str]:
    mods: list[str] = []
    for m in re.finditer(r'^(?:import|from)\s+([\w.]+)', content, re.MULTILINE):
        mods.append(m.group(1).split(".")[0].lower())
    return list(set(mods))


# ── Name normalisation for fuzzy matching ─────────────────────────────────────

def _base(name: str) -> str:
    """Strip extension and path; lowercase."""
    return PurePosixPath(name).stem.lower().replace("-", "_").replace(" ", "_")


# ── Heuristic rules ───────────────────────────────────────────────────────────

_ETL_PATTERNS = re.compile(r'(loader|etl|ingest|pipeline|transform|sync|load|writer)', re.I)
_REPORT_PATTERNS = re.compile(r'\.(dax|pbix|twbx|rdl)$|^(report|rpt|dashboard)', re.I)
_TEST_PATTERNS = re.compile(r'(^test_|_test\.|\.test\.|\.spec\.)', re.I)


def _heuristic_edges(entity: dict, all_by_base: dict[str, list[dict]]) -> list[tuple[str, str, str]]:
    """Return [(src_id, dst_id, relation)] from naming heuristics alone."""
    edges: list[tuple[str, str, str]] = []
    name = entity["name"]
    eid = entity["id"]
    b = _base(name)

    # ETL/loader scripts → WRITES_TO tables whose base name appears in the script name
    if entity["type"] == "Module" and _ETL_PATTERNS.search(name):
        for tgt in all_by_base.get(b.replace("_loader", "").replace("_etl", "").replace("_ingest", ""), []):
            if tgt["type"] == "Table" and tgt["id"] != eid:
                edges.append((eid, tgt["id"], "WRITES_TO"))
        # Also WRITES_TO all Table entities in other repos (snowflake convention)
        for key, targets in all_by_base.items():
            for tgt in targets:
                if tgt["type"] == "Table" and tgt["source_id"] != entity["source_id"]:
                    edges.append((eid, tgt["id"], "WRITES_TO"))

    # Report / DAX / BI files → READS_FROM tables by name
    if _REPORT_PATTERNS.search(name):
        for key, targets in all_by_base.items():
            for tgt in targets:
                if tgt["type"] == "Table" and tgt["source_id"] != entity["source_id"]:
                    edges.append((eid, tgt["id"], "READS_FROM"))

    # test_X → DEPENDS_ON module X
    if _TEST_PATTERNS.search(name) and entity["type"] == "Module":
        tested = re.sub(r'^test_|_test$', '', b)
        for tgt in all_by_base.get(tested, []):
            if tgt["type"] == "Module" and tgt["id"] != eid:
                edges.append((eid, tgt["id"], "DEPENDS_ON"))

    # Same-named Table across repos → DERIVED_FROM (later repo derives from earlier)
    if entity["type"] == "Table":
        for tgt in all_by_base.get(b, []):
            if tgt["type"] == "Table" and tgt["source_id"] != entity["source_id"] and tgt["id"] != eid:
                edges.append((eid, tgt["id"], "DERIVED_FROM"))

    return edges


# ── Route ─────────────────────────────────────────────────────────────────────

class OntologyResult(BaseModel):
    entities_scanned: int
    files_fetched: int
    edges_created: int
    relations: dict[str, int]
    message: str


@router.post(
    "/ontology/extract",
    response_model=OntologyResult,
    summary="Extract cross-source ontology relationships",
    description=(
        "Fetches file contents from all normalized sources, runs SQL/Python analysis, "
        "and writes cross-repository READS_FROM / WRITES_TO / DEPENDS_ON / DERIVED_FROM edges. "
        "Safe to re-run (idempotent)."
    ),
)
def extract_ontology(
    connection_factory: Any = Depends(connection_factory_dependency),
) -> OntologyResult:
    conn = connection_factory()
    try:
        cur = conn.cursor()

        # 1. Load all non-tombstoned entities with props
        cur.execute(
            "SELECT id, type, name, source_id, props FROM entities WHERE tombstoned_at IS NULL"
        )
        raw_entities = [
            {"id": str(r[0]), "type": r[1], "name": r[2], "source_id": str(r[3]),
             "props": (r[4] if isinstance(r[4], dict) else json.loads(r[4])) if r[4] else {}}
            for r in cur.fetchall()
        ]
        logger.info("ontology: loaded %d entities", len(raw_entities))

        # 2. Build lookup: base_name → [entity, ...]
        all_by_base: dict[str, list[dict]] = {}
        for e in raw_entities:
            key = _base(e["name"])
            all_by_base.setdefault(key, []).append(e)

        # 3. Collect edges
        new_edges: list[tuple[str, str, str]] = []  # (src_id, dst_id, relation)
        files_fetched = 0

        for entity in raw_entities:
            if entity["type"] == "Repository":
                continue

            # 3a. Heuristic edges (no fetch needed)
            new_edges.extend(_heuristic_edges(entity, all_by_base))

            # 3b. Content-based edges (fetch from GitHub)
            blob_url = entity["props"].get("uri", "")
            raw_url = _raw_url(blob_url) if blob_url else None
            if not raw_url:
                continue

            content = _fetch(raw_url)
            if content is None:
                continue
            files_fetched += 1

            if entity["type"] in ("Table",) or entity["name"].endswith(".sql"):
                reads, writes = _sql_refs(content)
                # Match extracted names against entity base names
                for ref_name in reads:
                    for tgt in all_by_base.get(ref_name, []):
                        if tgt["id"] != entity["id"] and tgt["type"] in ("Table", "Module"):
                            new_edges.append((entity["id"], tgt["id"], "READS_FROM"))
                for ref_name in writes:
                    for tgt in all_by_base.get(ref_name, []):
                        if tgt["id"] != entity["id"] and tgt["type"] == "Table":
                            new_edges.append((entity["id"], tgt["id"], "WRITES_TO"))

            elif entity["type"] == "Module" or entity["name"].endswith(".py"):
                imports = _py_imports(content)
                for mod_name in imports:
                    for tgt in all_by_base.get(mod_name, []):
                        if tgt["id"] != entity["id"] and tgt["type"] in ("Module", "Table"):
                            new_edges.append((entity["id"], tgt["id"], "DEPENDS_ON"))

            elif entity["name"].endswith((".dax", ".pbix", ".json", ".md")):
                # Look for entity name mentions in doc content
                for key, targets in all_by_base.items():
                    for tgt in targets:
                        if (tgt["type"] in ("Table", "Module")
                                and tgt["source_id"] != entity["source_id"]
                                and re.search(r'\b' + re.escape(key) + r'\b', content, re.I)):
                            rel = "READS_FROM" if tgt["type"] == "Table" else "DOCUMENTS"
                            new_edges.append((entity["id"], tgt["id"], rel))

        # 4. Deduplicate and write edges
        seen = set()
        edges_created = 0
        relation_counts: dict[str, int] = {}

        for src_id, dst_id, relation in new_edges:
            key = (src_id, dst_id, relation)
            if key in seen:
                continue
            seen.add(key)
            # Load source_id from either endpoint (use the src entity's source)
            src_entity = next((e for e in raw_entities if e["id"] == src_id), None)
            if not src_entity:
                continue
            source_id = src_entity["source_id"]
            try:
                cur.execute(
                    """
                    INSERT INTO edges
                      (src_entity_id, dst_entity_id, relation, confidence, source_id, ontology_version)
                    VALUES (%s, %s, %s, 0.85, %s, 'v0')
                    ON CONFLICT DO NOTHING
                    """,
                    (src_id, dst_id, relation, source_id),
                )
                edges_created += 1
                relation_counts[relation] = relation_counts.get(relation, 0) + 1
            except Exception as exc:
                logger.warning("edge insert failed %s→%s %s: %s", src_id, dst_id, relation, exc)
                conn.rollback()

        conn.commit()

        rel_summary = ", ".join(f"{k}:{v}" for k, v in sorted(relation_counts.items()))
        msg = (
            f"Scanned {len(raw_entities)} entities, fetched {files_fetched} files, "
            f"created {edges_created} edges ({rel_summary or 'none'})."
        )
        logger.info("ontology extraction done: %s", msg)
        return OntologyResult(
            entities_scanned=len(raw_entities),
            files_fetched=files_fetched,
            edges_created=edges_created,
            relations=relation_counts,
            message=msg,
        )
    finally:
        conn.close()
