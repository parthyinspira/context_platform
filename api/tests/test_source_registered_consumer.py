"""Consumer-side test for KAN-9: a source created through the API must be visible
to a consumer polling `source.registered` on the same `EventBus`, not just to a
mock that records the `publish` call. Uses the real `PostgresOutboxEventBus` over
the same in-memory fake DB-API connection already used by the adapter's own
contract tests, so this exercises the outbox round trip without a live Postgres.
"""
import uuid
from dataclasses import dataclass, field

from adapters.event_bus.postgres_outbox import PostgresOutboxEventBus
from adapters.tests.contract.fake_postgres import FakePostgresConnection
from app.main import app, connection_factory_dependency, event_bus_dependency
from fastapi.testclient import TestClient

VALID_PAYLOAD = {
    "type": "git_repo",
    "uri": "https://github.com/example/repo.git",
    "schedule": "0 * * * *",
    "credentials_ref": "git-repo-token",
    "owner": "platform-team",
    "sensitivity": "internal",
}


@dataclass
class FakeSourcesCursor:
    conn: "FakeSourcesConnection"
    _result: tuple | None = None

    def execute(self, sql: str, params: tuple) -> None:
        sql_norm = " ".join(sql.split())
        assert sql_norm.startswith("INSERT INTO sources"), f"unexpected SQL: {sql_norm}"
        type_, uri, schedule, credentials_ref, owner, sensitivity = params
        source_id = str(uuid.uuid4())
        self.conn.inserted.append(source_id)
        self._result = (
            source_id,
            type_,
            uri,
            schedule,
            credentials_ref,
            owner,
            sensitivity,
            "active",
        )

    def fetchone(self) -> tuple:
        return self._result


@dataclass
class FakeSourcesConnection:
    inserted: list[str] = field(default_factory=list)

    def cursor(self) -> FakeSourcesCursor:
        return FakeSourcesCursor(self)

    def commit(self) -> None:
        pass

    def close(self) -> None:
        pass


def test_consumer_receives_source_registered_event() -> None:
    sources_conn = FakeSourcesConnection()
    outbox_conn = FakePostgresConnection()
    event_bus = PostgresOutboxEventBus(lambda: outbox_conn)

    app.dependency_overrides[connection_factory_dependency] = lambda: (lambda: sources_conn)
    app.dependency_overrides[event_bus_dependency] = lambda: event_bus
    try:
        client = TestClient(app)
        response = client.post("/sources", json=VALID_PAYLOAD)
        assert response.status_code == 201
        source_id = response.json()["id"]

        received = event_bus.poll("source.registered", limit=10)

        assert len(received) == 1
        assert received[0].topic == "source.registered"
        assert received[0].payload == {"id": source_id}

        assert event_bus.poll("source.registered", limit=10) == []
    finally:
        app.dependency_overrides.clear()
