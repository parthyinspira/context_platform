from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException

from adapters.event_bus.base import EventBus
from adapters.factory import get_event_bus, get_secret_store
from app.db import get_connection_factory
from app.due import is_due
from app.schemas import DueSourceOut, RunOut

app = FastAPI(title="context-platform-scheduler")


def connection_factory_dependency() -> Any:
    """Open one DB connection for this request and return a zero-arg callable that
    always returns that same connection, so a route's writes and its `EventBus`
    (outbox) write share one connection/transaction and commit atomically.
    Overridden in tests with a fake so no live Postgres is required.
    """
    conn = get_connection_factory()()
    return lambda: conn


def event_bus_dependency(
    connection_factory: Any = Depends(connection_factory_dependency),
) -> EventBus:
    """Overridden in tests with a fake so no live Postgres is required."""
    return get_event_bus(connection_factory, get_secret_store())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sources/{source_id}/run", status_code=201, response_model=RunOut)
def run_source(
    source_id: str,
    connection_factory: Any = Depends(connection_factory_dependency),
    event_bus: EventBus = Depends(event_bus_dependency),
) -> RunOut:
    conn = connection_factory()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, type, uri, status FROM sources WHERE id = %s",
            (source_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="source not found")

        _id, source_type, uri, status = row
        if status != "active":
            raise HTTPException(
                status_code=409, detail=f"source is not active (status: {status})"
            )

        cur.execute(
            """
            INSERT INTO dispatcher_runs (source_id, status)
            VALUES (%s, 'queued')
            RETURNING id, source_id, status
            """,
            (source_id,),
        )
        run_row = cur.fetchone()
        run_id = str(run_row[0])
        # Same connection as the insert above: if this raises, the `finally` closes
        # without committing, so the run row is rolled back along with it.
        event_bus.publish(
            "harvest.requested",
            {
                "run_id": run_id,
                "source_id": source_id,
                "source_type": source_type,
                "uri": uri,
            },
        )
        conn.commit()
    finally:
        conn.close()

    return RunOut(id=run_id, source_id=str(run_row[1]), status=run_row[2])


@app.get("/sources/due", response_model=list[DueSourceOut])
def due_sources(
    connection_factory: Any = Depends(connection_factory_dependency),
) -> list[DueSourceOut]:
    conn = connection_factory()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, type, uri, schedule, last_harvest_at FROM sources WHERE status = 'active'"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    now = datetime.now(timezone.utc)
    return [
        DueSourceOut(
            id=str(row[0]),
            type=row[1],
            uri=row[2],
            last_harvest_at=row[4].isoformat() if row[4] else None,
        )
        for row in rows
        if is_due(row[3], row[4], now)
    ]
