# KAN-25: SQL lineage extraction with sqlglot (spike, time-boxed)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-25   Epic: 5 Ontology updater (KAN-23)   Branch: kan-25-sql-lineage-extraction-sqlglot

## Why
The ontology updater (Epic 5) needs deterministic extraction for SQL lineage before any LLM extraction is used, per CLAUDE.md ("Deterministic extraction first ... SQL lineage via sqlglot") and `docs/HARVESTERS.md` rule 9 ("Deterministic first, LLM second"). This is a time-boxed spike to prove that `sqlglot` can turn SQL text into `READS_FROM` / `WRITES_TO` facts that match Ontology v0, and to document what works, what doesn't, and whether to adopt it for the real Git/SQL harvesters (KAN-14, KAN-24, KAN-29) later in Epic 5.

## What changes
- Add a standalone, harvester-independent extraction module `ontology/sql_lineage.py` that parses one SQL statement (or a `;`-separated script) with `sqlglot` and returns `Table` entities and `READS_FROM` / `WRITES_TO` edges conforming to the Ontology v0 contract in CLAUDE.md (`type`, `source_id`, `external_id`, `props`, `ontology_version` on entities; `src_entity_id`/`dst_entity_id` by `external_id` reference, `relation`, `confidence`, `source_id`, `ontology_version` on edges).
- Statements that fail to parse are reported, not silently dropped (`unparsed` list with the raw statement and error), per "every record carries source_id" / manifest-everything conventions in `docs/HARVESTERS.md`.
- Document the spike outcome (what sqlglot handles, dialect/edge-case limitations found, and a recommendation for Epic 5) in `design.md`.
- No harvester, no database write, no API route, no UI change: this is a library-level spike. There is no `harvesters/` framework yet to plug into (confirmed: no `harvesters/` directory exists in the repo), so the extractor is intentionally a standalone, testable function the future SQL/Git harvester can call.

## In scope
- `ontology/sql_lineage.py`: `extract_sql_lineage(sql, source_id, ontology_version="v0") -> LineageResult` (dataclasses: `Entity`, `Edge`, `LineageResult`).
- Supports: `SELECT ... FROM`, `JOIN`, `INSERT INTO ... SELECT`, `UPDATE ... FROM`, `CREATE TABLE ... AS SELECT` (CTAS), `MERGE INTO ... USING`, CTEs (not emitted as entities, but their underlying base tables are).
- Deterministic only; no LLM call.
- Unit tests with small SQL fixtures (reads-only, writes-only, CTAS, CTE, multi-statement script, unparseable statement).
- `design.md`: the spike write-up (findings + recommendation), satisfying the AC "spike outcome documented".

## Out of scope
- Wiring this into a Git or SQL-database harvester (no harvester framework exists yet; tracked separately when Epic 2/3 harvesters land, per Build order in CLAUDE.md).
- Persisting entities/edges to Postgres (no normalizer exists yet; `entities`/`edges` tables exist per migration 0001 but nothing writes SQL-derived rows yet).
- Column-level lineage (table-level only, per Ontology v0 `READS_FROM`/`WRITES_TO` which are table-to-table relations).
- Non-SQL dialects beyond what `sqlglot`'s default dialect handles out of the box (dialect selection is a finding in `design.md`, not a feature built here).
- Confidence calibration beyond a fixed default (`0.9` deterministic-parse confidence); learned/variable confidence is future work.

## Acceptance criteria (from Jira)
1. SQL files yield READS_FROM/WRITES_TO edges -> scenarios: reads-from-select, writes-to-insert-select, writes-to-ctas, multi-statement-script
2. Spike outcome documented -> scenarios: spike-outcome-doc

## Affected
Capabilities: `spec/capabilities/sql-lineage-extraction.md` (new)   Docs/contracts: no change to the Postgres schema, Ontology v0 relation set, or the `Harvester` interface in CLAUDE.md — this spike produces data shaped to the existing Ontology v0 contract (Table entities, READS_FROM/WRITES_TO edges) without changing it. No Confluence Contracts update needed.

## Risks and open questions
- `sqlglot` is not yet a dependency anywhere in the repo; this story adds it only to the new `ontology/` package's `requirements.txt`, not repo-wide.
- Without a harvester to supply real `source_id`/`external_id` values, entity/edge `src_entity_id`/`dst_entity_id` in this spike are simple table-name-based external ids (e.g. `schema.table`), not real UUIDs from an `entities` table — documented as a known gap and a question for whoever wires this into a harvester (resolve `external_id` -> UUID at write time, not in the extractor).
- Dialect ambiguity (e.g. square-bracket identifiers vs backticks) may cause some real-world SQL to fail to parse; the spike documents this rather than trying to solve every dialect.

## Changes during development
- `story-reviewer` found a [blocking] bug at PR review: `WRITES_TO` edges were emitted as self-loops (`src_entity_id == dst_entity_id == write_external_id`) instead of `query -> table`, which is inconsistent with `READS_FROM`'s own `query -> table` convention and conveys no lineage fact. Fixed in `ontology/sql_lineage.py` (`WRITES_TO` now uses the same `"query"` proxy source as `READS_FROM`); added test assertions (`src != dst`, and that `WRITES_TO`/`READS_FROM` from one statement share the same `src`) so this cannot silently regress.

## Approval
Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
