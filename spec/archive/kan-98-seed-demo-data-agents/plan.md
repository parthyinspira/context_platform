# KAN-98: Seed demo data for agents (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-98   Branch: kepler/kan-98-seed-demo-data-agents

## Scope
In: Document harvester (`.md`, `.xlsx` → Document entity + Chunk); seed script that registers demo sources in Postgres, runs the document harvester for policy/FAQ docs, and inserts the lineage chain entities/edges (source_orders → stg_orders → mart_orders Dashboard, broken Job entity with `is_stale=true`); unit tests for the document harvester.
Out: Embeddings (seed uses `embedding_model='seed'`, embedding=NULL); agent loop code (KAN-99+); eval harness; running Docker for the seed (script runs against a reachable Postgres instance).

## Acceptance criteria (from Jira)
1. Lineage chain to dashboard: `source_orders → stg_orders → mart_orders` exist as entities with DERIVED_FROM edges; `mart_orders` is type Dashboard.
2. Broken job: `refresh_stg_orders` exists as a Job entity with `props.is_stale = true`.
3. Policy and FAQ documents loaded through the real document harvester: `data-retention-policy.md` (sensitivity=restricted) and `orders-faq.md` (sensitivity=internal) as Document entities with Chunks.

## Requirements
- The system SHALL provide a `DocumentHarvester` (source type `"document"`) that connects to a local directory, discovers `.md` and `.xlsx` files, harvests their content, normalizes each into a `Document` entity + one `Chunk`, and validates that all planned files were harvested. (Scenario: Given a directory with `orders-faq.md`; When the harvester runs; Then a Document entity and a Chunk with the body text exist.)
- The system SHALL provide `scripts/seed_demo.py` that, given a reachable Postgres DATABASE_URL, generates fixtures, registers three demo sources, runs the document harvester for the docs source, and upserts the lineage chain and broken-job entities/edges/chunks. (Scenario: Given a clean migrated Postgres; When `python scripts/seed_demo.py` runs; Then AC 1-3 all pass in the DB.)

## Tasks
- [x] 1. Create `harvesters/document/harvester.py` with `DocumentHarvester` (test first)
- [x] 2. Register `DocumentHarvester` in `harvesters/__init__.py`
- [x] 3. Create `scripts/seed_demo.py` (lineage chain, broken job, document harvester pass)
- [x] 4. Verify unit tests pass; run secret-scan

## Risks / not verifiable here
- Embeddings are NULL (no Ollama running during seed); retrieval quality not tested here.
- Docker compose integration (full `docker compose up` stack) is out of scope for this story per lite mode — the seed script targets a standalone Postgres instance.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
