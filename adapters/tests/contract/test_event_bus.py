from adapters.event_bus.postgres_outbox import PostgresOutboxEventBus

from .fake_postgres import FakePostgresConnection


def _bus() -> tuple[PostgresOutboxEventBus, FakePostgresConnection]:
    conn = FakePostgresConnection()
    return PostgresOutboxEventBus(lambda: conn), conn


def test_publish_and_poll_returns_event_once() -> None:
    bus, _ = _bus()
    bus.publish("source.registered", {"source_id": "abc"})

    first = bus.poll("source.registered", limit=10)
    second = bus.poll("source.registered", limit=10)

    assert len(first) == 1
    assert first[0].topic == "source.registered"
    assert first[0].payload == {"source_id": "abc"}
    assert second == []


def test_poll_respects_topic_and_limit() -> None:
    bus, _ = _bus()
    bus.publish("source.registered", {"n": 1})
    bus.publish("harvest.completed", {"n": 2})
    bus.publish("source.registered", {"n": 3})

    results = bus.poll("source.registered", limit=1)

    assert len(results) == 1
    assert results[0].payload == {"n": 1}
