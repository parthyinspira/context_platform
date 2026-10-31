from .loader import Ontology, load_ontology

ONTOLOGY = load_ontology()
ENTITY_TYPES = ONTOLOGY.entities
RELATION_TYPES = ONTOLOGY.relations
ONTOLOGY_VERSION = ONTOLOGY.version

__all__ = [
    "Ontology",
    "load_ontology",
    "ONTOLOGY",
    "ENTITY_TYPES",
    "RELATION_TYPES",
    "ONTOLOGY_VERSION",
]
