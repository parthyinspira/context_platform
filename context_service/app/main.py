from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import get_connection_factory

app = FastAPI(title="context-service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def connection_factory_dependency() -> Any:
    conn = get_connection_factory()()
    return lambda: conn


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Imported after the routes/dependencies above so these router modules can
# `from app.main import connection_factory_dependency` without a circular import.
from app.routes_entity import router as entity_router  # noqa: E402
from app.routes_lineage import router as lineage_router  # noqa: E402
from app.routes_search import router as search_router  # noqa: E402

app.include_router(search_router, tags=["search"])
app.include_router(lineage_router, tags=["lineage"])
app.include_router(entity_router, tags=["entity"])
