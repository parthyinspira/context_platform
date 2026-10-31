import json
import uuid
from typing import Any, Protocol

from .base import Event, EventBus


class DBConnection(Protocol):
    """Minimal DB-API-shaped connection (psycopg or any compatible driver)."""

    def cursor(self) -> Any: ...
    def commit(self) -> None: ...


class PostgresOutboxEventBus(EventBus):
    """Default EventBus: a Postgres `outbox_events` table, no message-broker SDK required.

    Takes a connection factory rather than a connection so each call gets a fresh
    connection/cursor, matching how `psycopg` pooled connections are typically used.
    """

    def __init__(self, connection_factory: "Any"):
        self._connection_factory = connection_factory

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        conn = self._connection_factory()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO outbox_events (id, topic, payload) VALUES (%s, %s, %s)",
            (str(uuid.uuid4()), topic, json.dumps(payload)),
        )
        conn.commit()

    def poll(self, topic: str, limit: int = 10) -> list[Event]:
        conn = self._connection_factory()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, topic, payload FROM outbox_events "
            "WHERE topic = %s AND delivered_at IS NULL "
            "ORDER BY created_at ASC LIMIT %s",
            (topic, limit),
        )
        rows = cur.fetchall()
        events = [
            Event(id=str(row[0]), topic=row[1], payload=row[2] if isinstance(row[2], dict) else json.loads(row[2]))
            for row in rows
        ]
        if events:
            ids = tuple(e.id for e in events)
            cur.execute(
                "UPDATE outbox_events SET delivered_at = now() WHERE id = ANY(%s)",
                (list(ids),),
            )
            conn.commit()
        return events
