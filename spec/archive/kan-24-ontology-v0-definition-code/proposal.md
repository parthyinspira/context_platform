# KAN-24: Ontology v0 definition in code and config

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-24   Epic: 5 Ontology updater (KAN-23)   Branch: kepler/kan-24-ontology-v0-definition-code

## Why
Epic 5 (ontology updater) and every harvester's `normalize()` step need one canonical, versioned list of entity and relation types instead of each piece of code hardcoding its own copy. Today the entity/relation list only exists as prose in `CLAUDE.md` and the Confluence Contracts page; there is no code or config any other module can import, so future stories would either duplicate the list or drift from it.

## What changes
- Add `adapters/ontology/v0.json`: the single source-of-truth file listing the versioned entity types and relation types for ontology v0.
- Add `adapters/ontology/loader.py` and `adapters/ontology/__init__.py`: a small loader exposing `ONTOLOGY`, `ENTITY_TYPES`, `RELATION_TYPES`, `ONTOLOGY_VERSION` so other modules import the types instead of hardcoding them.
- Add tests proving the file loads, is versioned, and its contents match `CLAUDE.md`'s "Ontology v0" section and the Confluence Contracts page.

## In scope
- One versioned definition file (`adapters/ontology/v0.json`) for entity and relation types, plus a thin Python loader.
- Tests that the loaded types match CLAUDE.md and Confluence exactly.

## Out of scope
- Any harvester, extraction, or ontology-updater logic (propose/validate/apply, `proposed_changes` handling, deterministic or LLM extraction). Those are later Epic 5 stories.
- Postgres schema changes (the `ontology_version` column already exists per KAN-4; this story does not touch migrations).
- A UI or MCP surface for the ontology.

## Acceptance criteria (from Jira)
KAN-24 description (the issue has no separate AC field; this is the full text): "AC: entity and relation types versioned and loaded from one file; matches Confluence."
1. Entity and relation types are versioned and loaded from one file -> scenarios: loads-from-one-file, versioned
2. Matches Confluence -> scenarios: matches-confluence-and-claude-md

## Affected
Capabilities: `spec/capabilities/ontology.md` (new)   Docs/contracts: none changed — this story codifies the existing Confluence Contracts page (Context Platform (Hackathon) - Project Home, section 4.3) and CLAUDE.md "Ontology v0" section; both already list the same entity/relation types, so no Confluence edit is required for this story.

## Risks and open questions
- No other module currently hardcodes entity/relation types (grepped the repo), so there is no existing duplicate to migrate onto this loader; future harvester/ontology-updater stories (KAN-23 epic) are expected to import from `adapters.ontology` instead of redefining the list.
- Confluence Contracts live as section 4.3 of the "Context Platform (Hackathon) – Project Home" page, not a separate "Contracts" child page as CLAUDE.md states; confirmed via the Confluence API that no such child page exists. Content checked is that section.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
