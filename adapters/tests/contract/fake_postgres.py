"""An in-memory fake of the tiny subset of psycopg's DB-API used by PostgresOutboxEventBus.

Used because no live Postgres is available in this environment; the real adapter issues
plain SQL against the `outbox_events` table from migration 0002 and is otherwise
untested against a live Postgres server (noted in verification.md).
"""
import json
from dataclasses import dataclass, field


@dataclass
class _Row:
    id: str
    topic: str
    payload: dict
    created_at: int
    delivered_at: bool = False


@dataclass
class FakePostgresConnection:
    rows: list[_Row] = field(default_factory=list)
    _seq: int = 0

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
        if sql_norm.startswith("INSERT INTO outbox_events"):
            row_id, topic, payload_json = params
            self._conn._seq += 1
            self._conn.rows.append(
                _Row(
                    id=row_id,
                    topic=topic,
                    payload=json.loads(payload_json),
                    created_at=self._conn._seq,
                )
            )
        elif sql_norm.startswith("SELECT id, topic, payload FROM outbox_events"):
            topic, limit = params
            matches = [r for r in self._conn.rows if r.topic == topic and not r.delivered_at]
            matches.sort(key=lambda r: r.created_at)
            self._result = [(r.id, r.topic, r.payload) for r in matches[:limit]]
        elif sql_norm.startswith("UPDATE outbox_events SET delivered_at"):
            (ids,) = params
            for r in self._conn.rows:
                if r.id in ids:
                    r.delivered_at = True
        else:
            raise AssertionError(f"unexpected SQL in fake: {sql_norm}")

    def fetchall(self) -> list[tuple]:
        return self._result
