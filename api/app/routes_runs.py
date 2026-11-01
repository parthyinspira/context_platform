"""Run create/read/stop and validation-report routes (KAN-58).

Reads and writes `harvest_runs` directly (plain SQL, no ORM, matching the
rest of the repo) — this is a thin layer in front of the table the one-off
runner (`harvesters/run.py`) also drives; it does not reimplement the
harvest lifecycle itself.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.main import connection_factory_dependency
from app.schemas_runs import (
    TERMINAL_RUN_STATES,
    LogEntryOut,
    ManifestSummaryOut,
    RunCreate,
    RunDetailOut,
    RunOut,
    ValidationReportOut,
)

router = APIRouter()


def _source_exists(connection_factory: Any, source_id: str) -> bool:
    conn = connection_factory()
    cur = conn.cursor()
    cur.execute("SELECT id FROM sources WHERE id = %s", (source_id,))
    return cur.fetchone() is not None


def _manifest_summary(manifest: dict[str, Any] | None) -> ManifestSummaryOut:
    entries = (manifest or {}).get("entries") or []
    summary = ManifestSummaryOut(discovered=len(entries))
    for entry in entries:
        outcome = entry.get("outcome")
        if outcome == "fetched":
            summary.fetched += 1
            summary.fetched_bytes += entry.get("size_bytes") or 0
        elif outcome == "skipped":
            summary.skipped += 1
        elif outcome == "failed":
            summary.failed += 1
    return summary


def _log_entries(manifest: dict[str, Any] | None) -> list[LogEntryOut]:
    entries = (manifest or {}).get("entries") or []
    return [
        LogEntryOut(
            ref=e["ref"], outcome=e.get("outcome"), outcome_reason=e.get("outcome_reason")
        )
        for e in entries
    ]


def _load_run_row(connection_factory: Any, run_id: str) -> tuple | None:
    conn = connection_factory()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, source_id, state, plan, manifest, error, report "
        "FROM harvest_runs WHERE id = %s",
        (run_id,),
    )
    return cur.fetchone()


def _run_detail_out(row: tuple) -> RunDetailOut:
    run_id, source_id, state, plan, manifest, error, _report = row
    return RunDetailOut(
        id=str(run_id),
        source_id=str(source_id),
        state=state,
        plan=plan or {},
        manifest_summary=_manifest_summary(manifest),
        log_entries=_log_entries(manifest),
        error=error,
    )


@router.post(
    "/sources/{source_id}/runs",
    status_code=201,
    response_model=RunOut,
    summary="Start a harvest run from an approved plan",
    description="Creates a harvest_runs row in state APPROVED with the given plan; "
    "a separate one-off harvester container (harvesters/run.py) drives it to completion.",
)
def create_run(
    source_id: str,
    request: RunCreate,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> RunOut:
    if not _source_exists(connection_factory, source_id):
        raise HTTPException(status_code=404, detail="source not found")
    conn = connection_factory()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO harvest_runs (source_id, state, plan) VALUES (%s, 'APPROVED', %s) "
        "RETURNING id, source_id, state",
        (source_id, json.dumps(request.plan.model_dump())),
    )
    row = cur.fetchone()
    conn.commit()
    return RunOut(id=str(row[0]), source_id=str(row[1]), state=row[2])


@router.get(
    "/runs/{run_id}",
    response_model=RunDetailOut,
    summary="Get a run's current status",
    description="Poll this endpoint for live state/manifest-count updates "
    "(no push/streaming transport exists yet).",
)
def get_run(
    run_id: str,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> RunDetailOut:
    row = _load_run_row(connection_factory, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    return _run_detail_out(row)


@router.patch(
    "/runs/{run_id}/stop",
    response_model=RunDetailOut,
    summary="Stop a non-terminal run",
    description="Best-effort: marks the run FAILED. Does not kill a running "
    "harvester container process (no job-control mechanism exists for that yet).",
)
def stop_run(
    run_id: str,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> RunDetailOut:
    row = _load_run_row(connection_factory, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    if row[2] in TERMINAL_RUN_STATES:
        raise HTTPException(status_code=409, detail=f"run already {row[2]}")

    conn = connection_factory()
    cur = conn.cursor()
    cur.execute(
        "UPDATE harvest_runs SET state = 'FAILED', error = %s, updated_at = now() "
        "WHERE id = %s RETURNING id, source_id, state, plan, manifest, error, report",
        ("stopped by user", run_id),
    )
    updated = cur.fetchone()
    conn.commit()
    return _run_detail_out(updated)


@router.get(
    "/runs/{run_id}/validation",
    response_model=ValidationReportOut,
    summary="Get a run's validation report",
    description="404 until a harvester populates harvest_runs.report; see "
    "spec/changes/kan-58-.../plan.md for why this is nullable today.",
)
def get_run_validation(
    run_id: str,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> ValidationReportOut:
    row = _load_run_row(connection_factory, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    report = row[6]
    if not report:
        raise HTTPException(status_code=404, detail="no validation report for this run yet")
    return ValidationReportOut(**report)
