from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from adapters.event_bus.base import EventBus
from adapters.factory import get_event_bus, get_secret_store
from app.db import get_connection_factory
from app.schemas import SourceCreate, SourceOut, SourceUpdate

app = FastAPI(title="context-platform-api")


def connection_factory_dependency() -> Any:
    """Open one DB connection for this request and return a zero-arg callable that
    always returns that same connection.

    The route and the `EventBus` (outbox) write must share one connection/transaction
    so the `sources` insert and the `source.registered` outbox row commit atomically —
    if they used separate connections, a crash between the two writes could leave a
    source row with no corresponding event. Overridden in tests with a fake so no
    live Postgres is required.
    """
    conn = get_connection_factory()()
    return lambda: conn


def event_bus_dependency(
    connection_factory: Any = Depends(connection_factory_dependency),
) -> EventBus:
    """Overridden in tests with a fake so no live Postgres is required."""
    return get_event_bus(connection_factory, get_secret_store())


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sources", status_code=201, response_model=SourceOut)
def create_source(
    source: SourceCreate,
    connection_factory: Any = Depends(connection_factory_dependency),
    event_bus: EventBus = Depends(event_bus_dependency),
) -> SourceOut:
    conn = connection_factory()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sources (type, uri, schedule, credentials_ref, owner, sensitivity, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'active')
            RETURNING id, type, uri, schedule, credentials_ref, owner, sensitivity, status
            """,
            (
                source.type,
                source.uri,
                source.schedule,
                source.credentials_ref,
                source.owner,
                source.sensitivity,
            ),
        )
        row = cur.fetchone()
        source_id = str(row[0])
        # Same connection as the insert above: if this raises, the `finally` closes
        # without committing, so the source row is rolled back along with it.
        event_bus.publish("source.registered", {"id": source_id})
        conn.commit()
    finally:
        conn.close()

    return _source_out_from_row(row)


def _source_out_from_row(row: tuple) -> SourceOut:
    return SourceOut(
        id=str(row[0]),
        type=row[1],
        uri=row[2],
        schedule=row[3],
        credentials_ref=row[4],
        owner=row[5],
        sensitivity=row[6],
        status=row[7],
    )


_SOURCE_COLUMNS = "id, type, uri, schedule, credentials_ref, owner, sensitivity, status"


@app.get("/sources", response_model=list[SourceOut])
def list_sources(
    connection_factory: Any = Depends(connection_factory_dependency),
) -> list[SourceOut]:
    conn = connection_factory()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT {_SOURCE_COLUMNS} FROM sources ORDER BY id")
        rows = cur.fetchall()
    finally:
        conn.close()
    return [_source_out_from_row(row) for row in rows]


@app.patch("/sources/{source_id}", response_model=SourceOut)
def update_source(
    source_id: str,
    update: SourceUpdate,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> SourceOut:
    conn = connection_factory()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT {_SOURCE_COLUMNS} FROM sources WHERE id = %s", (source_id,))
        current = cur.fetchone()
        if current is None:
            raise HTTPException(status_code=404, detail="source not found")

        new_schedule = update.schedule if update.schedule is not None else current[3]
        new_status = update.status if update.status is not None else current[7]

        cur.execute(
            "UPDATE sources SET schedule = %s, status = %s WHERE id = %s "
            f"RETURNING {_SOURCE_COLUMNS}",
            (new_schedule, new_status, source_id),
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()
    return _source_out_from_row(row)


@app.delete("/sources/{source_id}", response_model=SourceOut)
def delete_source(
    source_id: str,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> SourceOut:
    """Soft delete: sets `status=disabled` without removing the row."""
    conn = connection_factory()
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE sources SET status = 'disabled' WHERE id = %s RETURNING {_SOURCE_COLUMNS}",
            (source_id,),
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="source not found")
    return _source_out_from_row(row)
