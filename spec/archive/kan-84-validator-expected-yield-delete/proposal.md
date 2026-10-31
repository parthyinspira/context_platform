# KAN-84: Validator: expected yield, delete sanity, secrets/PII

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-84   Epic: 10 Harvester framework - planning, scoping, validation   Branch: kepler/kan-84-validator-expected-yield-delete

## Why
`docs/HARVESTERS.md` section 5 and `spec/capabilities/harvest-validation.md` describe ten validator checks, but only the publish/quarantine decision exists today (`harvest_validation/gate.py`, KAN-85) — it consumes a `ValidationReport.status` that nothing produces yet. The Jira AC for this story scopes three of the ten checks: expected yield (zero yield fails), delete sanity (a tombstone spike quarantines), and secrets/PII (unredacted secrets fail). The remaining seven checks (completeness, exclusion integrity, budget compliance, parse success, ontology conformance, referential integrity, freshness, spot check) need a real harvester manifest/profile shape to check against and are out of scope here, as `spec/archive/kan-85-publish-quarantine-gate/proposal.md` already flagged "the validator itself" as a separate, larger story.

## What changes
- New `harvest_validation/validator.py` with three pure, framework-independent checks, each returning a `CheckResult(status, detail, counts)`:
  - `check_expected_yield(detected_stacks, counts_by_type)`: FAILs if total entity yield is zero, or if a detected stack produced none of its expected ontology entity types (SQL/dbt -> Table, Java/.NET/Shell -> Module, Talend -> Job, Docs -> Document, per `docs/HARVESTERS.md` section 4). Unrecognized stacks are skipped (no expectation defined yet).
  - `check_delete_sanity(tombstoned_count, previously_published_count, threshold=0.2)`: FAILs when the tombstone share of previously-published objects exceeds the threshold (default 20%, per the capability spec's existing delete-spike scenario); PASSes when there is nothing previously published to compare against.
  - `check_secrets_and_pii(stored_texts)`: re-runs the existing `adapters.scanning.scan_and_redact` (KAN-82) over what was actually stored for each ref; FAILs listing any ref where a secret pattern is still present (defense in depth against a harvester that stored raw text without scanning first). PII alone (no secret) does not fail the check — the capability spec only requires sensitivity to be set for PII, which is out of scope here since no entity/sensitivity persistence exists yet.
  - `run_checks(...)` composes the three into a `harvesters.base.ValidationReport` (status FAIL if any check FAILs, else PASS), reusing the existing report shape so a future orchestrator can merge in the other seven checks later without a new type.
- Spec delta on `spec/capabilities/harvest-validation.md`: adds scenarios for zero-yield failure, stack-with-no-expected-entities failure, expected-yield pass, and unredacted-secret failure under "Standard checks"; the delete-spike scenario already exists and is left unchanged (this story implements it).

## In scope
- `check_expected_yield`, `check_delete_sanity`, `check_secrets_and_pii`, and `run_checks` in `harvest_validation/validator.py`, fully unit tested including fixture-based "deliberately broken" cases per `docs/HARVESTERS.md` section 7 (zero yield, delete spike, secret in stored text).
- Spec delta scenarios for the three checks named in the Jira AC.

## Out of scope
- The other seven validator checks (completeness, exclusion integrity, budget compliance, parse success, ontology conformance, referential integrity, freshness, spot check) — no manifest-driven harvester run exists yet to check them against.
- Wiring `run_checks` into a harvester's `validate()`, the dispatcher, or the `PublishQuarantineGate` — no concrete harvester or `harvest_runs` persistence exists yet (same constraint noted in KAN-85).
- Sensitivity persistence on entities/chunks for PII findings — no entity storage exists yet.
- Changing the delete-spike threshold or making it per-source configurable — the capability spec already fixes it at "more than 20 percent"; this story implements that number.

## Acceptance criteria (from Jira)
"Stack yields expected entity types (zero yield fails); tombstone spike over threshold quarantines; unredacted secrets fail."
1. Stack yields expected entity types (zero yield fails) -> scenarios: zero-yield-fails, stack-missing-expected-entities-fails, expected-yield-passes
2. Tombstone spike over threshold quarantines -> scenario: delete-spike (existing in capability spec; implemented by `check_delete_sanity`, exercised with a unit test and `run_checks` returning FAIL so the existing `PublishQuarantineGate` quarantines it)
3. Unredacted secrets fail -> scenario: unredacted-secret-fails

## Affected
Capabilities: `spec/capabilities/harvest-validation.md` (modified — adds scenarios under "Standard checks").   Docs/contracts: none changed (implements checks already named in `docs/HARVESTERS.md` section 5; no new contract).

## Risks and open questions
- No real harvester or manifest exists yet, so `run_checks` takes plain values (detected stacks, counts by type, tombstone counts, stored texts) rather than a `Manifest`/`Profile` object; a future story wires it to the real shapes. Flagged under "Not verified" at verification time.
- The stack-to-expected-entity-type mapping is a reasonable reading of `docs/HARVESTERS.md` section 4 but is not itself specified in Confluence; flagged for confirmation when a real Git harvester (KAN epic 3) lands.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR.
