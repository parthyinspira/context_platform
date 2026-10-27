# Context Platform

Hackathon project on Google Cloud: harvest registered sources (Git repos, documents, uploads) on a schedule, normalize them into Postgres (+ pgvector), keep an ontology/graph up to date, and serve context to agents via MCP.

Tracking: Jira project `KAN` (epics 1-8). Docs: Confluence space `SD`, page "Context Platform (Hackathon) - Project Home" and its child "Contracts". The Confluence Contracts page is the source of truth for the schema, ontology and harvester interface; update it in the same PR when you change any of them.

## Architecture
- Source registry (`sources` table) drives onboarding and scheduling. A new source is a row, never a code change.
- Harvesters run as Cloud Run Jobs, one per source type, launched by a dispatcher that Cloud Scheduler calls every few minutes.
- Pub/Sub topics: `source.registered`, `harvest.completed`, `ontology.updated`.
- Uploads land in Cloud Storage; object-finalize events publish to Pub/Sub.
- Raw payloads: Firestore (or GCS). Knowledge, edges and vectors: Cloud SQL Postgres + pgvector.
- Embeddings/LLMs through Vertex AI (Claude and Llama behind one config setting).
- Context service and MCP tools (`search_context`, `get_related`) run on Cloud Run.
- Secrets only in Secret Manager; one service account per component.

Flow: source registered -> harvester (discover/fetch/normalize) -> `harvest.completed` -> normalizer writes entities, edges, chunks, embeddings -> ontology updater (propose, validate, apply) -> `ontology.updated`.

## Contracts

### Harvester interface
```python
class Harvester:
    def discover(self, source) -> Iterable[ObjectRef]
    def fetch(self, source, ref, cursor) -> RawObject
    def normalize(self, raw) -> list[Entity | Edge | Chunk]
```
- Incremental via `sources.last_cursor`; upserts are idempotent, keyed by stable `external_id`.
- Objects not seen in a harvest get `tombstoned_at`; retrieval excludes tombstoned rows.
- Every record carries `source_id` and `harvested_at`.

### Ontology v0
- Entities: Repository, Service, Module, Table, Column, Dashboard, Job, Document, Person, Team.
- Relations: DEPENDS_ON, READS_FROM, WRITES_TO, DERIVED_FROM, DOCUMENTS, OWNED_BY, CONTAINS.
- Deterministic extraction first (manifests, SQL lineage via sqlglot, CODEOWNERS). LLM extraction only for unstructured text, constrained to this ontology, with a citation and confidence per assertion.
- New types or low-confidence facts go to `proposed_changes`; known types with high confidence auto-apply.
- Every fact stores `ontology_version`, `source_id`, `confidence`.

### Postgres schema v0
- `sources(id, type, uri, schedule, credentials_ref, owner, sensitivity, status, last_harvest_at, last_cursor, config_json)`
- `entities(id, type, name, source_id, external_id, props jsonb, ontology_version, tombstoned_at)`
- `edges(id, src_entity_id, dst_entity_id, relation, confidence, source_id, ontology_version)`
- `chunks(id, entity_id, source_id, text, embedding vector, embedding_model, metadata jsonb, harvested_at)`
- `proposed_changes(id, kind, payload jsonb, confidence, status, created_at)`

## Conventions
- Python 3.12, type hints, small modules. One harvester class per source type in `harvesters/`, registered by `source.type`.
- Schema changes go through migrations only. Never edit tables by hand.
- Record `embedding_model` on every chunk; chunk by structure (function, section, table), not fixed windows.
- Never store or log secret values; `credentials_ref` points to Secret Manager.
- Tests for every harvester (fixture repos/docs) and for idempotent re-harvest.
- Retrieval results always include source link, `harvested_at` and `sensitivity`.

## Workflow
1. Work one Jira story (`KAN-n`) per branch and PR; branch name `kan-<n>-short-slug`.
2. Read the story's acceptance criteria and the Confluence Contracts page first.
3. Implement with tests; run lint and tests before opening the PR.
4. Reference the story key in the PR title; update Confluence if a contract changed.
5. After merge, move the story to Done and add a one-line comment with the PR link.

## Build order
Epic 1 Foundation -> 2 Source registry/API -> 3 Git harvester -> 4 Scheduler/incremental -> 5 Ontology updater -> 6 Retrieval MCP -> 7 Upload harvester -> 8 Demo, evals, docs. Get a thin end-to-end demo working by the halfway point, even if rough.

## Security
Use a dedicated service account per harvester and only non-sensitive sample sources for the demo. Questions on access model, credentials or data flows go to the Inspira security team at security@inspirafinancial.com.

## Demo script
1. `POST /sources` with a new Git repo.
2. Watch harvest, normalization and ontology update complete.
3. Ask the agent a question only that repo can answer; check citations.
4. Upload a document and ask about it.
