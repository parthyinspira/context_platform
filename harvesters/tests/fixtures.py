"""Fixture harvester implementations used only by tests.

These register under fake, test-only source types so the real registry
(populated by real harvester packages added in later stories) is not
polluted by test state.
"""
from __future__ import annotations

from typing import Iterable

from harvesters.base import Chunk, Edge, Entity, Harvester, ObjectRef, RawObject
from harvesters.registry import register_harvester


class FixtureHarvester(Harvester):
    """A minimal, fully-implemented Harvester used to test the base contract."""

    def discover(self, source: dict) -> Iterable[ObjectRef]:
        return [ObjectRef(external_id="obj-1", path="obj-1.txt", size_bytes=10)]

    def fetch(self, source: dict, ref: ObjectRef, cursor: str | None) -> RawObject:
        return RawObject(external_id=ref.external_id, content=b"hello", content_type="text/plain")

    def normalize(self, raw: RawObject) -> list[Entity | Edge | Chunk]:
        return [
            Entity(type="Document", name=raw.external_id, external_id=raw.external_id),
            Chunk(entity_external_id=raw.external_id, text="hello"),
        ]


@register_harvester("fixture-type-a")
class RegisteredHarvesterA(FixtureHarvester):
    pass


@register_harvester("fixture-type-b")
class RegisteredHarvesterB(FixtureHarvester):
    pass


class IncompleteHarvester(Harvester):
    """Missing fetch/normalize on purpose, to test the ABC enforces the contract."""

    def discover(self, source: dict) -> Iterable[ObjectRef]:
        return []
