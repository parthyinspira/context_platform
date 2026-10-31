"""Fixture harvester implementations used only by tests.

These register under fake, test-only source types so the real registry
(populated by real harvester packages added in later stories) is not
polluted by test state.
"""
from __future__ import annotations

from typing import Any, Iterable

from harvesters.base import (
    Chunk,
    ConnectionResult,
    Edge,
    Entity,
    Harvester,
    ObjectRef,
    Profile,
    RawObject,
    ScopeNode,
    ScopeTree,
    ValidationReport,
)
from harvesters.framework import HarvestPlan
from harvesters.registry import register_harvester


class FixtureHarvester(Harvester):
    """A minimal, fully-implemented Harvester used to test the base contract."""

    def connect(self, source: dict) -> ConnectionResult:
        return ConnectionResult(ok=True)

    def discover(self, source: dict) -> ScopeTree:
        return ScopeTree(
            roots=[ScopeNode(id="obj-1", kind="file", name="obj-1.txt", size_hint=10)]
        )

    def profile(self, source: dict, scope: ScopeTree) -> Profile:
        refs = scope.refs()
        return Profile(object_count=len(refs), total_bytes=sum(r.size_bytes for r in refs))

    def plan(self, profile: Profile) -> HarvestPlan:
        return HarvestPlan()

    def harvest(
        self, source: dict, plan: HarvestPlan, cursor: str | None
    ) -> Iterable[RawObject]:
        for ref in ScopeTree(
            roots=[ScopeNode(id="obj-1", kind="file", name="obj-1.txt", size_hint=10)]
        ).refs():
            if plan.is_included(ref.path):
                yield RawObject(external_id=ref.external_id, content=b"hello", content_type="text/plain")

    def normalize(self, raw: RawObject) -> list[Entity | Edge | Chunk]:
        return [
            Entity(type="Document", name=raw.external_id, external_id=raw.external_id),
            Chunk(entity_external_id=raw.external_id, text="hello"),
        ]

    def validate(self, plan: HarvestPlan, manifest: list[dict[str, Any]]) -> ValidationReport:
        return ValidationReport(status="PASS")


@register_harvester("fixture-type-a")
class RegisteredHarvesterA(FixtureHarvester):
    pass


@register_harvester("fixture-type-b")
class RegisteredHarvesterB(FixtureHarvester):
    pass


class IncompleteHarvester(Harvester):
    """Missing several lifecycle methods on purpose, to test the ABC enforces the contract."""

    def discover(self, source: dict) -> ScopeTree:
        return ScopeTree()
