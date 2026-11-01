"""ContextClient: thin HTTP wrapper around the context service API.

Production code points this at CONTEXT_SERVICE_URL; tests inject a fake.
"""
from __future__ import annotations

from typing import Any, Protocol


class ContextTransport(Protocol):
    def get(self, url: str, params: dict[str, Any] | None = None) -> Any: ...


class ContextClient:
    """Wraps the context service HTTP API for the workflow agent."""

    def __init__(self, base_url: str, transport: ContextTransport) -> None:
        self._base = base_url.rstrip("/")
        self._transport = transport

    def search_context(self, query: str, limit: int = 10) -> list[dict]:
        return self._transport.get(
            f"{self._base}/search",
            params={"q": query, "limit": limit},
        )

    def get_lineage(self, entity_id: str, direction: str = "downstream", depth: int = 3) -> dict:
        return self._transport.get(
            f"{self._base}/lineage/{entity_id}",
            params={"direction": direction, "depth": depth},
        )

    def get_related(self, entity_id: str, relation: str | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if relation:
            params["relation"] = relation
        return self._transport.get(
            f"{self._base}/entities/{entity_id}/related",
            params=params,
        )
