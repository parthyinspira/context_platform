# Tasks

- [x] 1. Add failing tests in `adapters/tests/test_ontology.py` asserting: loads from one file, has a version, entity/relation types match CLAUDE.md/Confluence exactly, entities and relations are disjoint, and a missing file raises (scenarios: loads-from-one-file, versioned, matches-confluence-and-claude-md) - test first
- [x] 2. Add `adapters/ontology/v0.json` with the versioned entity and relation type lists (scenario: loads-from-one-file, versioned, matches-confluence-and-claude-md)
- [x] 3. Add `adapters/ontology/loader.py` (`Ontology` dataclass, `load_ontology()`) and `adapters/ontology/__init__.py` (`ONTOLOGY`, `ENTITY_TYPES`, `RELATION_TYPES`, `ONTOLOGY_VERSION`) (scenario: loads-from-one-file, versioned)
- [x] 4. Grep the repo for the entity/relation type names outside `adapters/ontology/` to confirm no other module hardcodes its own copy (scenario: no-duplicate-lists)
- [x] 5. Run `ruff check adapters` and `pytest adapters` (all tests, not just the new ones)
- [x] 6. Docs and contracts updated — none needed: CLAUDE.md and the Confluence Contracts page already state this ontology; this story only codifies it in code
- [x] 7. `verification.md` completed with evidence per scenario
