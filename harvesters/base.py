"""Harvester base class and the value types passed between its methods.

Implements the full lifecycle in `docs/HARVESTERS.md` section 1-2 and the
"Lifecycle" requirement in `spec/capabilities/harvester-framework.md`
(KAN-75), extending the original 3-method contract in `CLAUDE.md`:

    Connect -> Discover -> Profile -> Plan -> (approve) -> Harvest
    -> Validate -> Publish | Quarantine

`plan()` returns `harvesters.framework.HarvestPlan` (KAN-76) rather than a
new type, so the plan model and its budget enforcement stay in one place.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Optional

from harvesters.framework import HarvestPlan


class HarvestRunState(str, Enum):
    """The `harvest_runs.state` values, in lifecycle order (see migration 0004).

    This is the persisted state of one run's row, distinct from
    `harvesters.framework.budget.RunStatus`, which is an in-memory
    completed/partial signal from budget enforcement during `harvest()`.
    """

    CONNECTING = "CONNECTING"
    DISCOVERING = "DISCOVERING"
    PROFILING = "PROFILING"
    PLANNED = "PLANNED"
    APPROVED = "APPROVED"
    HARVESTING = "HARVESTING"
    VALIDATING = "VALIDATING"
    PUBLISHED = "PUBLISHED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class ObjectRef:
    """A reference to one discoverable object at a source, before it is fetched."""

    external_id: str
    path: str
    size_bytes: int = 0


@dataclass(frozen=True)
class ConnectionResult:
    """Output of `connect()`: whether a read-only identity was confirmed."""

    ok: bool
    error: str | None = None


@dataclass
class ScopeNode:
    """One discoverable item (repo, database, schema, site, workbook, ...)."""

    id: str
    kind: str
    name: str
    size_hint: int | None = None
    children: list["ScopeNode"] = field(default_factory=list)


@dataclass
class ScopeTree:
    """The scope shown to the user for approval, built from `discover()`."""

    roots: list[ScopeNode] = field(default_factory=list)

    def refs(self) -> list[ObjectRef]:
        """Flatten to `ObjectRef`s for `profile()`/`harvest()`, leaves only."""

        out: list[ObjectRef] = []

        def walk(node: ScopeNode) -> None:
            if node.children:
                for child in node.children:
                    walk(child)
            else:
                out.append(
                    ObjectRef(external_id=node.id, path=node.name, size_bytes=node.size_hint or 0)
                )

        for root in self.roots:
            walk(root)
        return out


@dataclass
class Profile:
    """Cheap scan of the chosen scope: sizes, file-type counts, detected stacks."""

    object_count: int
    total_bytes: int
    detected_stacks: list[str] = field(default_factory=list)
    counts_by_type: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class RawObject:
    """The fetched content for one `ObjectRef`."""

    external_id: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass(frozen=True)
class Entity:
    """Matches the `entities` table shape from the Postgres schema v0.

    `source_id`, `harvested_at` and `ontology_version` are optional (default
    `None`) so existing call sites that predate the validator (KAN-83) keep
    working; the validator's ontology-conformance check treats a missing
    value as a conformance failure once a harvester actually sets these.
    """

    type: str
    name: str
    external_id: str
    props: dict[str, Any] = field(default_factory=dict)
    source_id: str | None = None
    harvested_at: datetime | None = None
    ontology_version: str | None = None


@dataclass(frozen=True)
class Edge:
    """Matches the `edges` table shape from the Postgres schema v0.

    See `Entity` above for why `source_id`, `harvested_at` and
    `ontology_version` are optional.
    """

    src_external_id: str
    dst_external_id: str
    relation: str
    confidence: float = 1.0
    source_id: str | None = None
    harvested_at: datetime | None = None
    ontology_version: str | None = None


@dataclass(frozen=True)
class Chunk:
    """Matches the `chunks` table shape from the Postgres schema v0."""

    entity_external_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    harvested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ValidationReport:
    """Output of `validate()`; see `spec/capabilities/harvest-validation.md`."""

    status: str  # "PASS" | "WARN" | "FAIL"
    checks: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class Harvester(ABC):
    """Abstract base every source-type harvester implements.

    `source` is the `sources` table row (or an equivalent mapping) that
    identifies what to harvest; `cursor` is `sources.last_cursor`, used for
    incremental fetches.
    """

    @abstractmethod
    def connect(self, source: Any) -> ConnectionResult:
        """Test credentials with a read-only identity."""
        raise NotImplementedError

    @abstractmethod
    def discover(self, source: Any) -> ScopeTree:
        """List what is available at the source, metadata only (no content fetch)."""
        raise NotImplementedError

    @abstractmethod
    def profile(self, source: Any, scope: ScopeTree) -> Profile:
        """Cheap scan of the chosen scope: sizes, file-type counts, detected stacks."""
        raise NotImplementedError

    @abstractmethod
    def plan(self, profile: Profile) -> HarvestPlan:
        """Turn a profile into a harvest plan the user approves."""
        raise NotImplementedError

    @abstractmethod
    def harvest(
        self, source: Any, plan: HarvestPlan, cursor: Optional[str]
    ) -> Iterable[RawObject]:
        """Fetch only objects the plan allows, incrementally from `cursor`."""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw: RawObject) -> list[Entity | Edge | Chunk]:
        """Turn one fetched object into ontology records ready to upsert."""
        raise NotImplementedError

    @abstractmethod
    def validate(
        self, plan: HarvestPlan, manifest: list[dict[str, Any]]
    ) -> ValidationReport:
        """Check the run against the plan and manifest before publishing."""
        raise NotImplementedError
