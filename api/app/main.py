from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from adapters.event_bus.base import EventBus
from adapters.factory import get_event_bus, get_secret_store
from app.db import get_connection_factory
from app.schemas import SourceCreate, SourceOut

app = FastAPI(title="context-platform-api")


def connection_factory_dependency() -> Any:
    """Returns a zero-arg callable that opens a fresh DB connection per call.

    Overridden in tests with a fake so no live Postgres is required.
    """
    return get_connection_factory()


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
        conn.commit()
    finally:
        conn.close()

    source_id = str(row[0])
    event_bus.publish("source.registered", {"id": source_id})

    return SourceOut(
        id=source_id,
        type=row[1],
        uri=row[2],
        schedule=row[3],
        credentials_ref=row[4],
        owner=row[5],
        sensitivity=row[6],
        status=row[7],
    )
