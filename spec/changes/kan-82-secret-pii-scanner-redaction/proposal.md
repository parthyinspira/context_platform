# KAN-82: Secret and PII scanner with redaction

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-82   Epic: KAN-3 Git harvester (harvester framework "Read-only and secret-safe" rule)   Branch: kepler/kan-82-secret-pii-scanner-redaction

## Why
`spec/capabilities/harvester-framework.md` already requires "A harvester SHALL use read-only credentials and SHALL redact detected secrets before storage" and `docs/HARVESTERS.md` rule 8 ("Secrets and PII: scan fetched text for secrets ... and redact before storing; record a `sensitivity` on each object"), but no scanner exists yet. Harvester code (Epic 3) will need a ready-made module to call; `adapters/chunks/writer.py` is the one place today that persists harvested text (`chunks.text`), so it is the concrete storage boundary to wire this into now.

## What changes
- Add a deterministic secret/PII scanner module `adapters/scanning/scanner.py`: regex-based detection of common secrets (AWS access key IDs, AWS secret keys, generic API keys/tokens, Slack tokens, GitHub tokens, bearer tokens, PEM private key blocks, passwords in assignments and in connection-string URLs) and common PII (email, SSN, credit-card-shaped numbers), returning redacted text plus a derived `sensitivity` level (`restricted` if any secret found, `confidential` if only PII found, `internal` otherwise).
- Wire the scanner into `PostgresChunkWriter.write()` (`adapters/chunks/writer.py`): scan the text before embedding/storing, store the **redacted** text (never the raw secret), and merge the derived `sensitivity` plus a `redacted` flag into the stored `metadata` jsonb (no schema change — `chunks.metadata` is already `jsonb` per CLAUDE.md's Postgres schema v0).
- Unit tests for the scanner with seeded, clearly-fake secrets (fake AWS-shaped key, fake token, fake password, fake PEM block, fake email/SSN) proving detection, redaction and sensitivity derivation; an integration test proving `PostgresChunkWriter.write()` never persists the raw secret and sets `metadata.sensitivity`.

## In scope
- The scanner module (pure function, no I/O, no cloud SDK, no LLM).
- Wiring it into the one existing storage write path (`PostgresChunkWriter`).
- Tests with seeded fixture secrets (fake, non-real).

## Out of scope
- Any actual harvester (Epic 3, not built yet) — this module is built ahead of it per the existing capability requirement, for harvesters to call when they land.
- Validator wiring (`docs/HARVESTERS.md` "Secrets / PII" validator check) — that applies to the harvester validator, which doesn't exist yet; out of scope here.
- Entity-level `sources.sensitivity` changes, `proposed_changes`, or ontology changes.
- High-entropy/ML-based secret detection — regex-based deterministic detection only, matching "deterministic first" convention.
- A schema migration — `chunks.metadata` is already `jsonb`; sensitivity is stored there, not as a new column.

## Acceptance criteria (from Jira)
1. Detects keys, tokens, passwords in fetched text -> scenario: scanner flags seeded AWS key, generic API token, PEM private key, password assignment, connection-string password
2. Redacts before storage -> scenario: `PostgresChunkWriter.write()` stores redacted text, never the raw secret value
3. Sets sensitivity -> scenario: `metadata.sensitivity` is `restricted` when a secret is found, `confidential` when only PII is found, `internal` otherwise
4. Tested with seeded secrets -> scenario: unit tests use fake, clearly-non-real seeded secret values and assert detection + redaction + sensitivity

## Affected
Capabilities: spec/capabilities/harvester-framework.md (clarifies the existing "Read-only and secret-safe" requirement now has a concrete scanner implementation referenced)   Docs/contracts: none (no schema/ontology/harvester-interface change; `chunks.metadata` jsonb already supports this per CLAUDE.md)

## Risks and open questions
- Credit-card-shaped regex (`\b(?:\d[ -]*?){13,16}\b`) is broad and could over-match long digit sequences; flagged as a known false-positive risk, acceptable for a hackathon-scope deterministic PII check since it only affects `sensitivity`/redaction (safe direction to err in), not correctness of core data.
- No `harvesters/` package exists yet (Epic 3 not built), so there's no harvester call site to wire today beyond `PostgresChunkWriter`; future harvester work should call `adapters.scanning.scan_and_redact` on fetched text before normalization, per `docs/HARVESTERS.md` rule 8.

## Changes during development
(none)

## Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
