# KAN-68: Graph inspector: entity card with citations (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-68   Branch: kepler/kan-68-graph-inspector-entity-card

## Scope
In:
- A new `GET /entities/{id}` endpoint on the `api` service returning an entity's properties, its edges grouped by relation (with the neighbour's id/type/name and direction), its owner (from `sources.owner`), a source link and "open in source" link (from `sources.uri`), and a citation per chunk (source link, `harvested_at`, run id).
- A new `EntityCard` UI component (and `getEntity` API client function) matching `UI_DESIGN.md` 4.1 "Inspector (right): entity card with properties, edges grouped by relation, citations (source link, `harvested_at`, run id), owner, open in source", with empty/loading/error/success states per the UI capability's existing pattern.

Out:
- Wiring `EntityCard` into a live force-directed graph canvas/inspector panel (no `Graph` screen or Cytoscape canvas exists yet in `ui/`; that is graph-canvas work tracked separately). This story ships the inspector's entity-card component and its API, renderable standalone and tested in isolation, per the AC which names only the entity card.
- Tombstoned entities (excluded, 404, consistent with `GET /graph`).

## Acceptance criteria (from Jira/task)
1. Properties are shown.
2. Edges are grouped by relation.
3. Citations show source link, `harvested_at`, and run id.
4. Owner is shown.
5. "Open in source" is available.

## Requirements (only new or changed behaviour; at most 5)
- The `api` service SHALL provide `GET /entities/{id}` returning the entity's `props`, its edges grouped by `relation` (each with the neighbour entity and direction `out`/`in`), the owning source's `owner` and `uri` (used for "open in source"), and a `citations` list — one per chunk on the entity — each with the source's `uri`, the chunk's `harvested_at`, and a best-effort `run_id` (the most recent `harvest_runs` row for the source at or before `harvested_at`, or `null` if no run matches). Tombstoned entities SHALL 404.
  - Scenario: Given an entity with two edges (one outgoing DEPENDS_ON, one incoming CONTAINS) and one chunk, when `GET /entities/{id}` is called, then `edges_by_relation` has one entry per relation and `citations` has one entry with `source_link`, `harvested_at` and `run_id`.
  - Scenario: Given a tombstoned entity id, when `GET /entities/{id}` is called, then the response is 404.
- The `ui` service SHALL provide an `EntityCard` component accepting `state` (`empty`/`loading`/`error`/`success`) and entity data, rendering a key-value list of properties, edges grouped under a heading per relation, a citation chip per citation (source link, harvested_at, run id), the owner, and an "open in source" link to the source's `uri`.
  - Scenario: Given `state="success"` with props, grouped edges, citations and an owner, when rendered, then all of these appear and the "open in source" link's `href` is the source uri.
  - Scenario: Given `state="loading"`/`"error"`/`"empty"`, when rendered, then the shared `Skeleton`/`ErrorBanner`/`EmptyState` is shown instead of entity content.

## Tasks
- [x] 1. `api/tests/test_entity.py`: tests for `GET /entities/{id}` (props, edges grouped by relation with direction, citations with run id resolution, owner/source uri, 404 for missing/tombstoned) (test first).
- [x] 2. `api/app/schemas_entity.py` + `api/app/routes_entity.py`: implement the endpoint; register the router in `api/app/main.py`.
- [x] 3. `ui/test/EntityCard.test.jsx`: tests for all four states and the "open in source" link (test first).
- [x] 4. `ui/src/components/EntityCard.jsx`: implement the component using the shared `Skeleton`/`ErrorBanner`/`EmptyState` primitives.
- [x] 5. `ui/src/api.js`: add `getEntity(entityId)` calling `GET /entities/{id}`.
- [x] 6. Update `spec/capabilities/ui.md` with the new `EntityCard` requirement.

## Risks / not verifiable here
- Chunk-to-run attribution is best-effort (`harvest_runs.started_at <= chunk.harvested_at`, most recent match) because `chunks` does not store a `run_id` column; no migration is in scope for this story. Documented as a known limitation, not a blocking gap for the hackathon demo.
- `EntityCard` is not wired into a live graph canvas/inspector panel in this story (no such screen exists yet); it is verified standalone, matching the AC's scope (the entity card itself).
- No `docker compose up` run: this story only adds a route to an existing service and a UI component, neither touching the compose file.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
