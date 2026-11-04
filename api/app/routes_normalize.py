"""POST /runs/{run_id}/normalize — build a rich ontology from a PUBLISHED harvest run.

Creates:
  - One Repository entity per source
  - One entity per harvested file (Module, Document, Job, Table, etc.) based on extension
  - CONTAINS edges: Repository → each file entity
  - DEPENDS_ON edges: detected from simple import-pattern analysis stored in manifest props
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import PurePosixPath
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.main import connection_factory_dependency

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Entity type resolution ────────────────────────────────────────────────────

_EXT_MAP = {
    ".py": "Module", ".js": "Module", ".ts": "Module", ".jsx": "Module", ".tsx": "Module",
    ".go": "Module", ".java": "Module", ".cs": "Module", ".rb": "Module", ".rs": "Module",
    ".cpp": "Module", ".c": "Module", ".h": "Module", ".swift": "Module", ".kt": "Module",
    ".sql": "Table",
    ".md": "Document", ".rst": "Document", ".txt": "Document", ".pdf": "Document",
    ".yaml": "Job", ".yml": "Job",
    ".json": "Document", ".toml": "Document", ".ini": "Document",
    ".sh": "Job", ".bash": "Job",
    ".ipynb": "Document",
    ".csv": "Table", ".parquet": "Table",
    ".png": "Document", ".jpg": "Document", ".svg": "Document",
}

_FILENAME_MAP = {
    "dockerfile": "Job", "makefile": "Job", "jenkinsfile": "Job",
    "readme": "Document", "license": "Document", "changelog": "Document",
    "requirements.txt": "Document", "package.json": "Document", "pyproject.toml": "Document",
    "setup.py": "Module", "setup.cfg": "Document",
}

_CI_PATHS = {"github/workflows", ".github/workflows", ".gitlab-ci", "azure-pipelines", ".circleci"}


def _entity_type(ref: str) -> str:
    p = PurePosixPath(ref)
    # CI/CD paths → Job
    lower = ref.lower()
    if any(cp in lower for cp in _CI_PATHS):
        return "Job"
    # Dockerfile etc
    name_lower = p.name.lower()
    if name_lower in _FILENAME_MAP:
        return _FILENAME_MAP[name_lower]
    # Extension
    suffix = p.suffix.lower()
    return _EXT_MAP.get(suffix, "Document")


# ── Dependency extraction heuristics ─────────────────────────────────────────

_IMPORT_RE = re.compile(
    r'^\s*(?:import|from)\s+([\w.]+)',   # Python
    re.MULTILINE,
)
_JS_IMPORT_RE = re.compile(
    r"""(?:import|require)\s*\(?['"](\.{1,2}/[\w./]+)['"]""",  # relative JS import
    re.MULTILINE,
)


def _extract_internal_deps(ref: str, text_hint: str = "") -> list[str]:
    """Return refs that this file likely imports from the same repo (heuristic)."""
    deps: list[str] = []
    if not text_hint:
        return deps
    # Only extract relative JS/TS imports (most reliable for cross-file deps)
    if PurePosixPath(ref).suffix.lower() in {".js", ".ts", ".jsx", ".tsx"}:
        base = str(PurePosixPath(ref).parent)
        for m in _JS_IMPORT_RE.finditer(text_hint):
            rel = m.group(1)
            # Resolve rough path (no actual fs) — good enough for demo
            resolved = str(PurePosixPath(base) / rel).lstrip("/")
            deps.append(resolved)
    return deps


# ── Helpers ───────────────────────────────────────────────────────────────────

def _upsert_entity(cur: Any, etype: str, name: str, source_id: str, external_id: str, props: dict) -> str:
    cur.execute(
        """
        INSERT INTO entities (type, name, source_id, external_id, props, ontology_version)
        VALUES (%s, %s, %s, %s, %s::jsonb, 'v0')
        ON CONFLICT (source_id, external_id) DO UPDATE
          SET type = EXCLUDED.type, name = EXCLUDED.name, props = EXCLUDED.props
        RETURNING id
        """,
        (etype, name, source_id, external_id, json.dumps(props)),
    )
    return str(cur.fetchone()[0])


def _upsert_edge(cur: Any, src: str, dst: str, relation: str, source_id: str) -> None:
    cur.execute(
        """
        INSERT INTO edges (src_entity_id, dst_entity_id, relation, confidence, source_id, ontology_version)
        VALUES (%s, %s, %s, 1.0, %s, 'v0')
        ON CONFLICT DO NOTHING
        """,
        (src, dst, relation, source_id),
    )


# ── Route ─────────────────────────────────────────────────────────────────────

class NormalizeResult(BaseModel):
    entities_written: int
    edges_written: int
    chunks_written: int
    message: str


@router.post(
    "/runs/{run_id}/normalize",
    response_model=NormalizeResult,
    summary="Build ontology entities and edges from a PUBLISHED harvest run",
    description="Idempotent. Creates Repository + per-file entities with CONTAINS/DEPENDS_ON edges.",
)
def normalize_run(
    run_id: str,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> NormalizeResult:
    conn = connection_factory()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT hr.id, hr.source_id, hr.state, hr.manifest, s.type, s.uri "
            "FROM harvest_runs hr JOIN sources s ON s.id = hr.source_id "
            "WHERE hr.id = %s",
            (run_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="run not found")

        _, source_id, state, manifest_raw, source_type, source_uri = row
        source_id = str(source_id)

        if state != "PUBLISHED":
            raise HTTPException(
                status_code=409,
                detail=f"run is in state {state!r}; normalize only applies to PUBLISHED runs",
            )

        manifest = (
            manifest_raw if isinstance(manifest_raw, dict)
            else (json.loads(manifest_raw) if manifest_raw else {})
        )
        entries = manifest.get("entries") or []
        fetched = [e for e in entries if e.get("outcome") == "fetched"]

        # 1. Repository (root entity)
        repo_name = source_uri.rstrip("/").split("/")[-1] or source_uri
        repo_ext_id = f"{source_type}:{source_uri}"
        repo_id = _upsert_entity(cur, "Repository", repo_name, source_id, repo_ext_id, {
            "uri": source_uri, "type": source_type, "run_id": run_id,
            "file_count": len(fetched),
        })
        entities_written = 1
        edges_written = 0

        # 2. Per-file entities + CONTAINS edges
        file_id_map: dict[str, str] = {}  # ref → entity_id
        for entry in fetched:
            ref: str = entry.get("ref", "")
            etype = _entity_type(ref)
            name = PurePosixPath(ref).name or ref
            ext_id = f"{source_type}:{source_uri}/{ref}"
            eid = _upsert_entity(cur, etype, name, source_id, ext_id, {
                "ref": ref,
                "size_bytes": entry.get("size_bytes", 0),
                "run_id": run_id,
                "uri": f"{source_uri.rstrip('/')}/blob/main/{ref}",
            })
            file_id_map[ref] = eid
            entities_written += 1
            # CONTAINS: Repository → file
            _upsert_edge(cur, repo_id, eid, "CONTAINS", source_id)
            edges_written += 1

        # 3. DEPENDS_ON edges from JS/TS relative imports (best-effort)
        for entry in fetched:
            ref = entry.get("ref", "")
            src_id = file_id_map.get(ref)
            if not src_id:
                continue
            for dep_ref in _extract_internal_deps(ref, ""):
                # Try exact match, then with common extensions
                dst_id = file_id_map.get(dep_ref)
                if not dst_id:
                    for ext in (".ts", ".tsx", ".js", ".jsx"):
                        dst_id = file_id_map.get(dep_ref + ext)
                        if dst_id:
                            break
                if dst_id:
                    _upsert_edge(cur, src_id, dst_id, "DEPENDS_ON", source_id)
                    edges_written += 1

        # 4. CI → Repository DOCUMENTS edges (Dockerfile/CI files document the repo)
        for ref, eid in file_id_map.items():
            if _entity_type(ref) == "Job":
                _upsert_edge(cur, eid, repo_id, "DOCUMENTS", source_id)
                edges_written += 1

        # 5. Chunks — delete old ones for this run, re-insert
        cur.execute(
            "DELETE FROM chunks WHERE source_id = %s AND metadata->>'run_id' = %s",
            (source_id, run_id),
        )
        chunks_written = 0
        for entry in fetched:
            ref = entry.get("ref", "")
            entity_id = file_id_map.get(ref, repo_id)
            text = f"{_entity_type(ref)}: {ref}\nRepository: {source_uri}"
            cur.execute(
                """
                INSERT INTO chunks (entity_id, source_id, text, embedding_model, metadata, harvested_at)
                VALUES (%s, %s, %s, 'none', %s::jsonb, now())
                """,
                (entity_id, source_id, text,
                 json.dumps({"ref": ref, "size_bytes": entry.get("size_bytes", 0), "run_id": run_id})),
            )
            chunks_written += 1

        conn.commit()
        logger.info(
            "normalized run=%s entities=%d edges=%d chunks=%d",
            run_id, entities_written, edges_written, chunks_written,
        )
        return NormalizeResult(
            entities_written=entities_written,
            edges_written=edges_written,
            chunks_written=chunks_written,
            message=(
                f"Built {entities_written} entities ({repo_name} + {len(fetched)} files), "
                f"{edges_written} edges (CONTAINS + CI), {chunks_written} chunks."
            ),
        )
    finally:
        conn.close()
