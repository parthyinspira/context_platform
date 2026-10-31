"""One-off harvester runner / container entrypoint (KAN-16).

Drives one registered `Harvester` through connect -> discover -> harvest ->
normalize -> validate for one already-`PLANNED`/`APPROVED` `harvest_runs`
row, writing state transitions back to `harvest_runs` and publishing
`harvest.completed` on the `EventBus` when done.

"plan_id" in the KAN-16 acceptance criteria is the `harvest_runs.id` of that
row: no separate `plans` table exists, and the plan itself already lives on
`harvest_runs.plan` (migration `0004_harvest_runs.up.sql`). See
`spec/changes/kan-16-run-harvester-one-off-container-job/proposal.md` for why.

Persisting the `Entity`/`Edge`/`Chunk` records `normalize()` returns to
Postgres is the job of a separate, future normalizer consuming
`harvest.completed` (per the flow in `CLAUDE.md`), not this runner.

Packaged (see `harvesters/Dockerfile`) so the same container image runs
unmodified via `docker compose run harvester`, a GCP Cloud Run Job or an
Azure Container Apps Job: all three pass per-task configuration as
environment variables rather than positional container-command arguments,
so `SOURCE_ID`/`PLAN_ID`/`DATABASE_URL` are read from the environment by
default, with CLI flags available for local/manual runs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import psycopg

from adapters.event_bus.base import EventBus
from adapters.factory import get_event_bus, get_secret_store
from harvest_validation.gate import PublishQuarantineGate, RunState, ValidationStatus
from harvesters.base import Chunk, Edge, Entity, Harvester, HarvestRunState
from harvesters.framework.manifest import Manifest
from harvesters.framework.plan import Budgets, HarvestPlan
from harvesters.registry import UnknownSourceTypeError, get_harvester

HARVEST_COMPLETED_TOPIC = "harvest.completed"


class RunnerError(RuntimeError):
    """Raised for any condition that should abort the run before it starts mutating state."""


class HarvestRunNotFoundError(RunnerError):
    """No `harvest_runs` row matches the given plan id (and source id)."""


def get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RunnerError("DATABASE_URL must be set")
    return database_url


def get_connection_factory() -> Any:
    """Return a zero-arg callable that opens a fresh connection per call.

    Matches the `connection_factory` pattern already used by
    `adapters.event_bus.postgres_outbox.PostgresOutboxEventBus` and
    `scheduler/app/db.py`.
    """
    database_url = get_database_url()
    return lambda: psycopg.connect(database_url)


def _plan_from_dict(data: dict[str, Any]) -> HarvestPlan:
    budgets_data = data.get("budgets") or {}
    return HarvestPlan(
        include=tuple(data.get("include") or ()),
        exclude=tuple(data.get("exclude") or ()),
        size_cap_bytes=data.get("size_cap_bytes"),
        budgets=Budgets(
            max_files=budgets_data.get("max_files"),
            max_bytes=budgets_data.get("max_bytes"),
            max_seconds=budgets_data.get("max_seconds"),
            max_tokens=budgets_data.get("max_tokens"),
        ),
    )


def _as_json_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return json.loads(value)


class HarvestRunStore:
    """Reads/writes one `harvest_runs` row and its `sources` row through a
    DB-API connection factory (plain SQL, no ORM, matching the rest of the repo)."""

    def __init__(self, connection_factory: Any):
        self._connection_factory = connection_factory

    def load_plan(self, plan_id: str, source_id: str) -> HarvestPlan:
        conn = self._connection_factory()
        cur = conn.cursor()
        cur.execute(
            "SELECT source_id, plan FROM harvest_runs WHERE id = %s",
            (plan_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise HarvestRunNotFoundError(f"no harvest_runs row with id {plan_id!r}")
        row_source_id, plan_json = row
        if str(row_source_id) != str(source_id):
            raise HarvestRunNotFoundError(
                f"harvest_runs {plan_id!r} belongs to source {row_source_id!r}, "
                f"not the requested source {source_id!r}"
            )
        return _plan_from_dict(_as_json_dict(plan_json))

    def load_source(self, source_id: str) -> dict[str, Any]:
        conn = self._connection_factory()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, type, uri, last_cursor, config_json FROM sources WHERE id = %s",
            (source_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise HarvestRunNotFoundError(f"no source with id {source_id!r}")
        return {
            "id": str(row[0]),
            "type": row[1],
            "uri": row[2],
            "last_cursor": row[3],
            "config_json": _as_json_dict(row[4]),
        }

    def set_state(
        self,
        run_id: str,
        state: HarvestRunState,
        *,
        manifest: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        conn = self._connection_factory()
        cur = conn.cursor()
        if manifest is not None:
            cur.execute(
                "UPDATE harvest_runs SET state = %s, manifest = %s, error = %s, "
                "updated_at = now() WHERE id = %s",
                (state.value, json.dumps(manifest), error, run_id),
            )
        else:
            cur.execute(
                "UPDATE harvest_runs SET state = %s, error = %s, updated_at = now() "
                "WHERE id = %s",
                (state.value, error, run_id),
            )
        conn.commit()


def _run_lifecycle(
    harvester: Harvester,
    source: dict[str, Any],
    plan: HarvestPlan,
    manifest: Manifest,
) -> list[Entity | Edge | Chunk]:
    """Connect, discover, harvest and normalize; raises on a failed connect.

    Fetch/normalize failures for an individual object are recorded on the
    manifest as `failed` rather than aborting the whole run, so one bad
    object does not take down an otherwise-good harvest (the validator's
    completeness check is what judges whether the resulting ratio still
    passes).
    """
    connection_result = harvester.connect(source)
    if not connection_result.ok:
        raise RunnerError(f"connect failed: {connection_result.error}")

    scope = harvester.discover(source)
    for ref in scope.refs():
        manifest.discovered(ref.external_id, reason="discovered", size_bytes=ref.size_bytes)

    records: list[Entity | Edge | Chunk] = []
    cursor = source.get("last_cursor")
    for raw in harvester.harvest(source, plan, cursor):
        try:
            records.extend(harvester.normalize(raw))
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            manifest.failed(raw.external_id, reason=f"normalize failed: {exc}")
            continue
        manifest.fetched(raw.external_id, reason="fetched and normalized")

    return records


def run(
    source_id: str,
    plan_id: str,
    *,
    connection_factory: Any = None,
    event_bus: EventBus | None = None,
) -> HarvestRunState:
    """Run the full lifecycle for one source/plan; returns the final state.

    `connection_factory`/`event_bus` default to the real Postgres/`EventBus`
    adapters built from the environment; tests inject fakes here instead of
    monkeypatching module globals, the same seam `scheduler/app/main.py` uses
    via FastAPI `Depends`.

    Raises `RunnerError`/`HarvestRunNotFoundError` for conditions that abort
    before any `harvest_runs` write (unknown plan id, bad config); once the
    run has started, every other failure is caught and recorded as `FAILED`
    on the row instead of propagating, so the container always leaves the
    row in a terminal state and always attempts to publish `harvest.completed`.
    """
    if connection_factory is None:
        connection_factory = get_connection_factory()
    if event_bus is None:
        event_bus = get_event_bus(connection_factory, get_secret_store())
    store = HarvestRunStore(connection_factory)

    # Let "unknown plan id"/"wrong source"/"no harvester registered" abort before any
    # state write: there is nothing yet to mark FAILED, and a typo'd id or an
    # unregistered source type should not conjure a new row.
    plan = store.load_plan(plan_id, source_id)
    source = store.load_source(source_id)
    try:
        harvester = get_harvester(source["type"])
    except UnknownSourceTypeError as exc:
        raise RunnerError(str(exc)) from exc

    manifest = Manifest(source_id=source_id, run_id=plan_id)

    try:
        store.set_state(plan_id, HarvestRunState.HARVESTING)
        records = _run_lifecycle(harvester, source, plan, manifest)

        store.set_state(plan_id, HarvestRunState.VALIDATING, manifest=manifest.to_dict())
        manifest_entries = [e.to_dict() for e in manifest.entries()]
        report = harvester.validate(plan, manifest_entries)

        gate_result = PublishQuarantineGate().evaluate(
            RunState.VALIDATING, ValidationStatus(report.status)
        )
        final_state = HarvestRunState(gate_result.new_state.value)
        error = "; ".join(report.errors) if report.errors else None
        store.set_state(plan_id, final_state, manifest=manifest.to_dict(), error=error)

        event_bus.publish(
            HARVEST_COMPLETED_TOPIC,
            {
                "run_id": plan_id,
                "source_id": source_id,
                "state": final_state.value,
                "published": gate_result.published,
                "warning": gate_result.warning,
                "reason": gate_result.reason,
                "entity_count": sum(1 for r in records if isinstance(r, Entity)),
                "edge_count": sum(1 for r in records if isinstance(r, Edge)),
                "chunk_count": sum(1 for r in records if isinstance(r, Chunk)),
            },
        )
        return final_state
    except Exception as exc:  # noqa: BLE001 - last line of defense for a job container
        store.set_state(
            plan_id, HarvestRunState.FAILED, manifest=manifest.to_dict(), error=str(exc)
        )
        event_bus.publish(
            HARVEST_COMPLETED_TOPIC,
            {
                "run_id": plan_id,
                "source_id": source_id,
                "state": HarvestRunState.FAILED.value,
                "published": False,
                "warning": False,
                "reason": str(exc),
            },
        )
        return HarvestRunState.FAILED


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a harvest for one source_id/plan_id to completion."
    )
    parser.add_argument("--source-id", default=os.environ.get("SOURCE_ID"))
    parser.add_argument("--plan-id", default=os.environ.get("PLAN_ID"))
    args = parser.parse_args(argv)
    if not args.source_id:
        parser.error("--source-id (or SOURCE_ID) is required")
    if not args.plan_id:
        parser.error("--plan-id (or PLAN_ID) is required")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        final_state = run(args.source_id, args.plan_id)
    except RunnerError as exc:
        print(f"harvester run aborted: {exc}", file=sys.stderr)
        return 2
    print(f"harvester run finished: {final_state.value}")
    # PUBLISHED and QUARANTINED are both a lifecycle that ran to completion and reached
    # a gate decision; only FAILED (connect error or unhandled exception) is a job failure.
    return 0 if final_state in (HarvestRunState.PUBLISHED, HarvestRunState.QUARANTINED) else 1


if __name__ == "__main__":
    raise SystemExit(main())
