"""Harvester interface shared by every source-type pack (KAN-75).

Matches the lifecycle and interface in `docs/HARVESTERS.md` section 1-2 and the
"Lifecycle" requirement in `spec/capabilities/harvester-framework.md`. This module
defines the contract only: value types and an abstract base class. Concrete
harvesters (Git, SQL, SharePoint, ...) live in their own `harvesters/<system>/`
packs and are added by later stories.

Cloud-neutral: no cloud SDK imports, no I/O.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HarvestRunState(str, Enum):
    """The `harvest_runs.state` values, in lifecycle order (see migration 0004)."""

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


@dataclass
class ConnectionResult:
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
    roots: list[ScopeNode] = field(default_factory=list)


@dataclass
class Profile:
    """Cheap scan of the chosen scope: sizes, file-type counts, detected stacks."""

    object_count: int
    total_bytes: int
    detected_stacks: list[str] = field(default_factory=list)
    counts_by_type: dict[str, int] = field(default_factory=dict)


@dataclass
class HarvestPlan:
    """Include/exclude patterns, caps and budgets derived from a `Profile`."""

    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    budgets: dict[str, int] = field(default_factory=dict)
    skipped: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RawObject:
    ref: str
    content: bytes
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    type: str
    name: str
    external_id: str
    props: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    relation: str
    src_external_id: str
    dst_external_id: str
    confidence: float = 1.0


@dataclass
class Chunk:
    entity_external_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    status: str  # "PASS" | "WARN" | "FAIL"
    checks: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class Harvester(ABC):
    """Lifecycle contract every source-type harvester implements.

    Connect -> Discover -> Profile -> Plan -> (approve) -> Harvest -> Normalize -> Validate.
    """

    @abstractmethod
    def connect(self, source: Any) -> ConnectionResult:
        """Test credentials with a read-only identity."""

    @abstractmethod
    def discover(self, source: Any) -> ScopeTree:
        """List what is available at the source, metadata only."""

    @abstractmethod
    def profile(self, source: Any, scope: ScopeTree) -> Profile:
        """Cheap scan of the chosen scope."""

    @abstractmethod
    def plan(self, profile: Profile) -> HarvestPlan:
        """Turn a profile into a harvest plan the user approves."""

    @abstractmethod
    def harvest(self, source: Any, plan: HarvestPlan, cursor: str | None) -> list[RawObject]:
        """Fetch only objects the plan allows, incrementally from `cursor`."""

    @abstractmethod
    def normalize(self, raw: RawObject) -> list[Entity | Edge | Chunk]:
        """Turn one fetched object into entities, edges and/or chunks."""

    @abstractmethod
    def validate(self, plan: HarvestPlan, manifest: list[dict[str, Any]]) -> ValidationReport:
        """Check the run against the plan and manifest before publishing."""
