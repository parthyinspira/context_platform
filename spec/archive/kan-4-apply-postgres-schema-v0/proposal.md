# KAN-4: Apply Postgres schema v0 with migrations

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-4   Epic: KAN-1 Foundation   Branch: kan-4-apply-postgres-schema-v0

## Why
KAN-101 stood up the compose stack (Postgres+pgvector, api, ui, scheduler, embeddings) but the database has no application schema yet — only the `vector` extension. Every later epic (source registry API, harvesters, ontology updater, retrieval MCP) depends on the five core tables existing and being reachable the same way on a fresh database. Schema changes must go through migrations only (CLAUDE.md), so this story adds the first repeatable migration set.

## What changes
- Add a migration tool/runner convention under `migrations/` (forward + down SQL per change, applied in order, tracked in a migration-history table so re-running is a no-op).
- Add migration(s) that create `sources`, `entities`, `edges`, `chunks`, `proposed_changes` with the columns listed in CLAUDE.md's "Postgres schema v0" section.
- Enable `vector` extension as part of the migration set (superseding the existing `scripts/init-db/001-pgvector.sql` one-off) so a fresh database only needs migrations run.
- Add a migration test that applies from empty, re-applies (idempotent/no-op), and rolls back.
- Update the Confluence Contracts page to match (tracked as a task; content mirrors CLAUDE.md, which is already the source of the column list).

## In scope
- The migration runner/convention and the migration files for the five v0 tables and their constraints/indexes.
- A documented way to run migrations against the compose Postgres service (`docker compose run` or an `api`/one-off container command).
- Minimal indexes needed for the FK/lookup patterns named in CLAUDE.md (`source_id`, `external_id`, `tombstoned_at`).
- Migration test(s).

## Out of scope
- Any API endpoints reading/writing these tables (source registry API is KAN-5+).
- Ontology extraction logic, harvesters, embeddings generation.
- Seed/demo data.
- Changing `docker-compose.yml` service topology.

## Acceptance criteria (from Jira)
1. Tables `sources`, `entities`, `edges`, `chunks`, `proposed_changes` are created by a repeatable migration -> scenarios: fresh database, idempotent re-run, rollback
2. Schema matches the Confluence Contracts page -> scenarios: columns match contract, Confluence updated

## Affected
Capabilities: spec/capabilities/postgres-schema.md (new)   Docs/contracts: CLAUDE.md ("Postgres schema v0" — already accurate, used as the source for the migration), Confluence space SD page "Contracts"

## Risks and open questions
- No migration tool is chosen yet for this repo (e.g. plain numbered `.sql` files run by a small Python runner vs. a library like `yoyo`/`alembic`). Proposal: plain forward/down `.sql` files under `migrations/`, applied by a small Python script (consistent with the existing `scripts/init-db` pattern and CLAUDE.md's "small modules" convention, no new heavy dependency). Flagging for approval.
- `chunks.embedding` needs a fixed vector dimension for pgvector (`vector(n)`); no embedding model has been chosen yet for the dimension. Proposal: use a placeholder dimension (1536, overridable later via a follow-up migration) and record this as an open question rather than blocking the story.

## Changes during development
(none)

## Approval
Approved by: parthasarathy.venkatachalam, 2026-10-30
