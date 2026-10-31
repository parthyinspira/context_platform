"""Loads Ontology v0 from the single JSON file that is the source of truth.

Entity and relation types must match CLAUDE.md's "Ontology v0" section and the
Confluence Contracts page (Context Platform (Hackathon) - Project Home, section 4.3).
Any code needing these types SHALL import `ONTOLOGY` (or `ENTITY_TYPES` /
`RELATION_TYPES`) from this package instead of hardcoding its own list.
"""
import json
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_PATH = Path(__file__).parent / "v0.json"


@dataclass(frozen=True)
class Ontology:
    version: str
    entities: tuple[str, ...]
    relations: tuple[str, ...]


def load_ontology(path: Path = _DEFAULT_PATH) -> Ontology:
    data = json.loads(path.read_text())
    return Ontology(
        version=data["version"],
        entities=tuple(data["entities"]),
        relations=tuple(data["relations"]),
    )
