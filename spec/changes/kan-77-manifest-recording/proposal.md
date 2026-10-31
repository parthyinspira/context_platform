# KAN-77: Manifest recording

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-77   Epic: KAN-74 (Epic 10: Harvester framework - planning, scoping, validation)   Branch: kepler/kan-77-manifest-recording

## Why
`docs/HARVESTERS.md` rule 11 says "Everything is manifested. Every discovered, fetched, skipped and failed object is recorded with a reason. The validator depends on this." Several validator checks (completeness, exclusion integrity, budget reporting) and the Git harvest story (KAN-80, "writes manifest") need one shared, cloud-neutral manifest model to write to and read from. No manifest model exists yet. When planning started there was no `harvesters/` package on `main`; KAN-12 (base class, registry) and KAN-76 (plan, budgets) have since landed in `harvesters/` and `harvesters/framework/`.

## What changes
- New framework module `harvesters/framework/manifest.py`, exported from `harvesters.framework` (no source-type harvester yet).
- `Manifest`: per-run record of objects keyed by a stable ref (path or `external_id`). Recording methods for the four outcomes: `discovered`, `fetched`, `skipped`, `failed`. A non-empty reason is required for every record.
- Outcome rules: an object must be discovered before it gets an outcome (discover before download); each discovered object gets at most one outcome (`fetched`, `skipped` or `failed`); repeating the identical record is a no-op so a resumed run can replay it; a conflicting outcome is rejected.
- Reasons go through the shared scanner (`adapters.scanning.scan_and_redact`) before they are stored, so error text holding a secret (for example a connection string) is never kept.
- Read API for the validator: entries by outcome, counts per outcome, and `unaccounted()` (discovered objects that have no outcome yet). Counts and sample failures feed the validator report later.
- JSON serialization and a `ManifestStore` that saves and loads a manifest through the existing `ObjectStore` interface, key `manifests/<source_id>/<run_id>.json`.
- CI: add `harvesters` to the lint and Python test matrix; `pyproject.toml` ruff include.

## In scope
- `harvesters/framework/manifest.py`, `harvesters/framework/__init__.py` (exports), `harvesters/tests/test_manifest.py`; package scaffold (`harvesters/__init__.py`, `requirements*.txt`) if not already on `main`.
- `.github/workflows/ci.yml` and `pyproject.toml` entries for the new package.
- Spec delta for `harvester-framework` (requirement "Manifest recording").

## Out of scope
- Harvester interface extension, `harvest_runs` table and run states (KAN-75, KAN-12). `run_id` is an opaque string supplied by the caller until `harvest_runs` exists.
- Harvest plan, include/exclude rules and budgets (KAN-76). The manifest records whatever reason the caller gives; it does not decide what to skip.
- Validator checks and `ValidationReport` (KAN-83, KAN-84). This story provides the manifest read API they consume; it does not implement the checks.
- Git harvester writing the manifest (KAN-80).
- Any Postgres schema change. The manifest is stored as a JSON object through `ObjectStore` (CLAUDE.md: "Uploads and raw payloads use an `ObjectStore` interface"), so no migration and no Contracts page change.
- UI display of the manifest.

## Acceptance criteria (from Jira)
1. "every discovered, fetched, skipped and failed object recorded with reason" -> scenarios: record every outcome with reason, reason required, discover before outcome, one outcome per object, secret in a reason is redacted
2. "used by the validator" -> scenarios: validator reads outcomes and unaccounted objects, manifest persisted and reloaded per run

## Affected
Capabilities: `spec/capabilities/harvester-framework.md` (ADDED requirement "Manifest recording")   Docs/contracts: `docs/HARVESTERS.md` rule 11 gained a note on the manifest format (added in review round 1); no contract changed. The `Harvester` interface signatures in CLAUDE.md and `docs/HARVESTERS.md` are unchanged; `validate(plan, manifest, results)` already names a manifest, and this story defines its shape. No schema, ontology or Confluence Contracts change.

## Risks and open questions
- At planning time KAN-75, KAN-12, KAN-76 and KAN-83 were all To Do; KAN-12 and KAN-76 merged during this story, while KAN-75 and KAN-83 are still open. Assumption: KAN-77 is built first as a standalone module that those stories integrate; "used by the validator" is satisfied by the read API plus tests that consume it the way the validator will. KAN-83 may still ask for extra read helpers; it can add them.
- Manifest location (ObjectStore JSON rather than a Postgres table) is a design choice; if the team prefers a `harvest_manifest` table, that is a later migration story.
- Branch is `kepler/kan-77-manifest-recording` (Kepler prefix) rather than plain `kan-77-manifest-recording`; branched from `main` d3a6344, then `origin/main` c2fe45e (KAN-12, KAN-76) was merged in during review round 2.

## Changes during development
- Review round 1 (story-reviewer, APPROVE WITH NITS) led to these changes, all inside this story's scope:
  - Loading a stored manifest now enforces the recording rules (reason required, outcome needs a reason, no duplicate refs) and redacts reasons.
  - `ManifestStore.load` rejects a body whose `source_id`/`run_id` differ from the key, and forwards an injected clock.
  - The end-to-end check over `fixtures/repos/java-sample` is now an in-repo test.
  - New delta scenario "loaded manifest obeys the recording rules".
  - `docs/HARVESTERS.md` rule 11 now documents the manifest format and key. This is a doc note only; the interface signatures are unchanged.
- Review round 2 (story-reviewer, CHANGES REQUESTED):
  - The one blocking finding was an add/add conflict in `harvesters/__init__.py` after KAN-12/KAN-76 merged. Resolved by merging `origin/main` and keeping main's docstring. This PR's CI, `pyproject.toml` and package-scaffold edits now match main.
  - The module moved to `harvesters/framework/manifest.py` to follow main's layout, and is exported from `harvesters.framework`.
  - Malformed stored files (missing keys, bad dates, unknown outcome, non-dict entries) now raise `ManifestError`, and a bool `size_bytes` is rejected.
  - Left for KAN-80: refs are not scanned for secrets (only reasons are, per the spec). A Git harvester using URLs with userinfo as refs should strip credentials first.
- Not done here: the reviewer flagged an I001 lint error in `api/tests/test_source_registered_consumer.py` that is already on main. It is outside this story and is left for a separate fix.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
