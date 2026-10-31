# Capability: ontology

### Requirement: Versioned single-file definition
Ontology v0's entity and relation types SHALL be defined in exactly one file and SHALL carry a version identifier.
#### Scenario: loads-from-one-file
- **Given** `adapters/ontology/v0.json`
- **When** `adapters.ontology.load_ontology()` is called
- **Then** it returns an `Ontology` with non-empty `entities` and `relations` tuples

#### Scenario: versioned
- **Given** the loaded ontology
- **When** its `version` field is read
- **Then** it equals `"v0"`

### Requirement: Matches the documented contract
The loaded entity and relation types SHALL match the "Ontology v0" section of `CLAUDE.md` and the Confluence Contracts page exactly.
#### Scenario: matches-confluence-and-claude-md
- **Given** the loaded ontology
- **When** its `entities` and `relations` are compared to CLAUDE.md's "Ontology v0" list and to section 4.3 of the Confluence "Context Platform (Hackathon) – Project Home" page
- **Then** both lists match exactly: entities Repository, Service, Module, Table, Column, Dashboard, Job, Document, Person, Team; relations DEPENDS_ON, READS_FROM, WRITES_TO, DERIVED_FROM, DOCUMENTS, OWNED_BY, CONTAINS

### Requirement: Single source consumed, not duplicated
Code needing entity or relation type names SHALL import them from `adapters.ontology` rather than hardcoding a second list.
#### Scenario: no-duplicate-lists
- **Given** the repository source tree
- **When** it is searched for the entity/relation type names outside `adapters/ontology/` and `CLAUDE.md`/Confluence/spec docs
- **Then** no other Python module hardcodes its own copy of the list
