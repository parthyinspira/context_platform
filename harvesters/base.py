"""Harvester base class and the value types passed between its methods.

Implements the harvester interface defined in `CLAUDE.md`:

    class Harvester:
        def discover(self, source) -> Iterable[ObjectRef]
        def fetch(self, source, ref, cursor) -> RawObject
        def normalize(self, raw) -> list[Entity | Edge | Chunk]

This module intentionally implements only those three methods. The fuller
`connect/discover/profile/plan/harvest/normalize/validate` lifecycle described
in `docs/HARVESTERS.md` and `spec/capabilities/harvester-framework.md` is a
later extension of this base, built out alongside a concrete harvester
(starting with Git).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class ObjectRef:
    """A reference to one discoverable object at a source, before it is fetched."""

    external_id: str
    path: str
    size_bytes: int = 0


@dataclass(frozen=True)
class RawObject:
    """The fetched content for one `ObjectRef`."""

    external_id: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass(frozen=True)
class Entity:
    """Matches the `entities` table shape from the Postgres schema v0."""

    type: str
    name: str
    external_id: str
    props: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    """Matches the `edges` table shape from the Postgres schema v0."""

    src_external_id: str
    dst_external_id: str
    relation: str
    confidence: float = 1.0


@dataclass(frozen=True)
class Chunk:
    """Matches the `chunks` table shape from the Postgres schema v0."""

    entity_external_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    harvested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Harvester(ABC):
    """Abstract base every source-type harvester implements.

    `source` is the `sources` table row (or an equivalent mapping) that
    identifies what to harvest; `cursor` is `sources.last_cursor`, used for
    incremental fetches.
    """

    @abstractmethod
    def discover(self, source: Any) -> Iterable[ObjectRef]:
        """List objects available at the source, metadata only (no content fetch)."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self, source: Any, ref: ObjectRef, cursor: Optional[str]) -> RawObject:
        """Fetch the content for one discovered object."""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw: RawObject) -> list[Entity | Edge | Chunk]:
        """Turn one fetched object into ontology records ready to upsert."""
        raise NotImplementedError
