import pytest

from harvesters.base import Chunk, Edge, Entity, Harvester, ObjectRef, RawObject


def test_cannot_instantiate_base_class_directly():
    with pytest.raises(TypeError):
        Harvester()  # type: ignore[abstract]


def test_cannot_instantiate_incomplete_subclass():
    class Incomplete(Harvester):
        def discover(self, source):
            return []

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_base_class_contract_full_implementation():
    class Complete(Harvester):
        def discover(self, source):
            return [ObjectRef(external_id="o1", path="o1.txt", size_bytes=1)]

        def fetch(self, source, ref, cursor):
            return RawObject(external_id=ref.external_id, content=b"x", content_type="text/plain")

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

    h = Complete()
    refs = list(h.discover(source={"type": "fixture", "uri": "x"}))
    assert refs == [ObjectRef(external_id="o1", path="o1.txt", size_bytes=1)]

    raw = h.fetch(source={}, ref=refs[0], cursor=None)
    assert raw.external_id == "o1"
    assert raw.content == b"x"

    records = h.normalize(raw)
    assert isinstance(records[0], Entity)
    assert isinstance(records[1], Edge)
    assert isinstance(records[2], Chunk)
