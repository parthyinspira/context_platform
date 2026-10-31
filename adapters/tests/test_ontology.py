from pathlib import Path

import pytest

from adapters.ontology import (
    ENTITY_TYPES,
    ONTOLOGY_VERSION,
    RELATION_TYPES,
    Ontology,
    load_ontology,
)

EXPECTED_ENTITIES = (
    "Repository",
    "Service",
    "Module",
    "Table",
    "Column",
    "Dashboard",
    "Job",
    "Document",
    "Person",
    "Team",
)

EXPECTED_RELATIONS = (
    "DEPENDS_ON",
    "READS_FROM",
    "WRITES_TO",
    "DERIVED_FROM",
    "DOCUMENTS",
    "OWNED_BY",
    "CONTAINS",
)


def test_ontology_loads_from_single_file():
    ontology = load_ontology()
    assert isinstance(ontology, Ontology)


def test_ontology_is_versioned():
    assert ONTOLOGY_VERSION == "v0"


def test_entity_types_match_confluence_and_claude_md():
    assert ENTITY_TYPES == EXPECTED_ENTITIES


def test_relation_types_match_confluence_and_claude_md():
    assert RELATION_TYPES == EXPECTED_RELATIONS


def test_entity_and_relation_types_are_disjoint():
    assert set(ENTITY_TYPES).isdisjoint(set(RELATION_TYPES))


def test_module_level_constants_are_the_same_load_as_load_ontology():
    reloaded = load_ontology()
    assert reloaded.entities == ENTITY_TYPES
    assert reloaded.relations == RELATION_TYPES
    assert reloaded.version == ONTOLOGY_VERSION


def test_load_ontology_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_ontology(tmp_path / "does-not-exist.json")
