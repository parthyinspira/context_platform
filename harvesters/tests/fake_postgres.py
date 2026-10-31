"""An in-memory fake of the tiny psycopg subset `harvesters.run.HarvestRunStore` uses.

Used because no live Postgres is available in this environment; mirrors
`adapters/tests/contract/fake_postgres.py`'s shape but models `sources` and
`harvest_runs` rows instead of the outbox.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeSource:
    id: str
    type: str
    uri: str = "fake://source"
    last_cursor: str | None = None
    config_json: dict = field(default_factory=dict)


@dataclass
class FakeHarvestRun:
    id: str
    source_id: str
    state: str = "APPROVED"
    plan: dict = field(default_factory=dict)
    manifest: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class FakePostgresConnection:
    sources: dict[str, FakeSource] = field(default_factory=dict)
    runs: dict[str, FakeHarvestRun] = field(default_factory=dict)
    state_history: list[str] = field(default_factory=list)

    def cursor(self) -> "FakePostgresCursor":
        return FakePostgresCursor(self)

    def commit(self) -> None:
        pass


class FakePostgresCursor:
    def __init__(self, conn: FakePostgresConnection):
        self._conn = conn
        self._result: list[tuple] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
        sql_norm = " ".join(sql.split())
        if sql_norm.startswith("SELECT source_id, plan FROM harvest_runs"):
            (run_id,) = params
            run = self._conn.runs.get(run_id)
            self._result = [(run.source_id, json.dumps(run.plan))] if run else []
        elif sql_norm.startswith("SELECT id, type, uri, last_cursor, config_json FROM sources"):
            (source_id,) = params
            source = self._conn.sources.get(source_id)
            self._result = (
                [
                    (
                        source.id,
                        source.type,
                        source.uri,
                        source.last_cursor,
                        json.dumps(source.config_json),
                    )
                ]
                if source
                else []
            )
        elif sql_norm.startswith("UPDATE harvest_runs SET state = %s, manifest = %s"):
            state, manifest_json, error, run_id = params
            run = self._conn.runs[run_id]
            run.state = state
            run.manifest = json.loads(manifest_json)
            run.error = error
            self._conn.state_history.append(state)
        elif sql_norm.startswith("UPDATE harvest_runs SET state = %s, error = %s"):
            state, error, run_id = params
            run = self._conn.runs[run_id]
            run.state = state
            run.error = error
            self._conn.state_history.append(state)
        else:
            raise AssertionError(f"unexpected SQL in fake: {sql_norm}")

    def fetchone(self) -> tuple | None:
        return self._result[0] if self._result else None

    def fetchall(self) -> list[tuple]:
        return self._result


class FakeEventBus:
    """Records published events; no `poll()` needed for these tests."""

    def __init__(self) -> None:
        self.published: list[tuple[str, dict[str, Any]]] = []

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.published.append((topic, payload))

    def poll(self, topic: str, limit: int = 10) -> list:
        raise NotImplementedError
