from datetime import UTC, datetime

import pytest

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


def test_entity_and_edge_carry_optional_provenance_fields():
    harvested_at = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)

    entity = Entity(
        type="Table",
        name="orders",
        external_id="orders",
        source_id="src-1",
        harvested_at=harvested_at,
        ontology_version="v0",
    )
    edge = Edge(
        src_external_id="a",
        dst_external_id="b",
        relation="READS_FROM",
        source_id="src-1",
        harvested_at=harvested_at,
        ontology_version="v0",
    )

    assert entity.source_id == "src-1"
    assert entity.harvested_at == harvested_at
    assert entity.ontology_version == "v0"
    assert edge.source_id == "src-1"
    assert edge.harvested_at == harvested_at
    assert edge.ontology_version == "v0"


def test_entity_and_edge_default_provenance_fields_to_none():
    entity = Entity(type="Table", name="orders", external_id="orders")
    edge = Edge(src_external_id="a", dst_external_id="b", relation="READS_FROM")

    assert entity.source_id is None
    assert entity.harvested_at is None
    assert entity.ontology_version is None
    assert edge.source_id is None
    assert edge.harvested_at is None
    assert edge.ontology_version is None


def test_cannot_instantiate_base_class_directly():
    with pytest.raises(TypeError):
        Harvester()  # type: ignore[abstract]


def test_cannot_instantiate_incomplete_subclass():
    class Incomplete(Harvester):
        def discover(self, source):
            return ScopeTree()

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_base_class_contract_full_implementation():
    class Complete(Harvester):
        def connect(self, source):
            return ConnectionResult(ok=True)

        def discover(self, source):
            return ScopeTree(roots=[ScopeNode(id="o1", kind="file", name="o1.txt", size_hint=1)])

        def profile(self, source, scope):
            refs = scope.refs()
            return Profile(object_count=len(refs), total_bytes=sum(r.size_bytes for r in refs))

        def plan(self, profile):
            return HarvestPlan()

        def harvest(self, source, plan, cursor):
            return [RawObject(external_id="o1", content=b"x", content_type="text/plain")]

        def normalize(self, raw):
            return [
                Entity(type="Document", name=raw.external_id, external_id=raw.external_id),
                Edge(
                    src_external_id=raw.external_id,
                    dst_external_id=raw.external_id,
                    relation="CONTAINS",
                ),
                Chunk(entity_external_id=raw.external_id, text="x"),
            ]

        def validate(self, plan, manifest):
            return ValidationReport(status="PASS")

    h = Complete()
    conn = h.connect(source={"type": "fixture", "uri": "x"})
    assert conn.ok is True

    scope = h.discover(source={"type": "fixture", "uri": "x"})
    refs = scope.refs()
    assert refs == [ObjectRef(external_id="o1", path="o1.txt", size_bytes=1)]

    profile = h.profile(source={}, scope=scope)
    assert profile.object_count == 1

    plan = h.plan(profile)
    assert isinstance(plan, HarvestPlan)

    raw_objects = list(h.harvest(source={}, plan=plan, cursor=None))
    assert raw_objects[0].external_id == "o1"
    assert raw_objects[0].content == b"x"

    records = h.normalize(raw_objects[0])
    assert isinstance(records[0], Entity)
    assert isinstance(records[1], Edge)
    assert isinstance(records[2], Chunk)

    report = h.validate(plan, manifest=[])
    assert report.status == "PASS"
