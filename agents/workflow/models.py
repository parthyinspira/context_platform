"""Domain models for the workflow change-request impact agent."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChangeTicket:
    entity_name: str
    entity_type: str
    change_description: str


@dataclass
class Citation:
    source_link: str
    harvested_at: str
    sensitivity: str


@dataclass
class DownstreamAsset:
    entity_id: str
    entity_name: str
    entity_type: str
    relation: str
    depth: int
    citation: Citation


@dataclass
class Owner:
    entity_id: str
    entity_name: str
    citation: Citation


@dataclass
class ImpactReport:
    ticket: ChangeTicket
    downstream_assets: list[DownstreamAsset] = field(default_factory=list)
    owners: list[Owner] = field(default_factory=list)
    suggested_approvers: list[str] = field(default_factory=list)
    suggested_tests: list[str] = field(default_factory=list)
    draft_comment: str = ""
