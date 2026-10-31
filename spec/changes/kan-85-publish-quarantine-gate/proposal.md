# KAN-85: Publish or quarantine gate

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-85   Epic: 10 Harvester framework - planning, scoping, validation   Branch: kepler/kan-85-publish-quarantine-gate

## Why
`docs/HARVESTERS.md` and `spec/capabilities/harvest-validation.md` already describe that a validator produces `PASS | WARN | FAIL` and that the gate decides whether a run's knowledge is published or quarantined. The capability spec currently only has a scenario for `FAIL`; there is no scenario or implementation for `WARN`, for the normal `PASS` path, or for guarding which run states the gate may act on. Nothing in the repo implements this decision today (confirmed: no `harvest_runs` table or harvester code exists yet — per `spec/archive/kan-106-dispatcher-run-endpoint-ui/proposal.md`, the full `harvest_runs` lifecycle table is scoped to this harvest-core epic, stories 75/12/76/77/85).

## What changes
- New `harvest_validation` package with a pure, framework-independent `PublishQuarantineGate`:
  - Input: the run's current state (must be `VALIDATING`) and a `ValidationReport`-like status (`PASS | WARN | FAIL`) plus optional check findings.
  - Output: a `GateResult` with the new run state (`PUBLISHED` or `QUARANTINED`), whether knowledge should be published, whether a warning should be shown, and a human-readable reason.
  - `FAIL` -> `QUARANTINED`, `published=False` (previous knowledge untouched).
  - `WARN` -> `PUBLISHED`, `published=True`, `warning=True`.
  - `PASS` -> `PUBLISHED`, `published=True`, `warning=False`.
  - Calling the gate from any state other than `VALIDATING` raises `InvalidRunStateError` (guards the state machine; nothing today drives a run into `VALIDATING`, so this is a defensive contract check, tested directly).
- `RunState` enum reusing the state names already named in `spec/capabilities/harvester-framework.md` (`CONNECTING, DISCOVERING, PROFILING, PLANNED, APPROVED, HARVESTING, VALIDATING, PUBLISHED, QUARANTINED, FAILED`) so a future `harvest_runs` persistence layer can adopt it without renaming.
- Spec delta on `spec/capabilities/harvest-validation.md`: adds the `WARN` and `PASS` scenarios and a new "State transitions" requirement.

## In scope
- The gate's decision logic for `PASS`/`WARN`/`FAIL` and the state-transition guard, fully unit tested.
- Spec delta scenarios for all three validator outcomes plus the invalid-state-transition scenario.

## Out of scope
- The `harvest_runs` table/migration and any persistence of run state — scoped to later harvest-core stories (KAN-75/12/76/77) per the dispatcher-run precedent above; this gate is pure logic a future orchestrator will call and persist the result of.
- The `ValidationReport` producer itself (the validator that runs the checks listed in `docs/HARVESTERS.md` section 5) — a different, larger story; this change only consumes a report's `status` field.
- Wiring the gate into the scheduler/dispatcher or UI — no caller exists yet.

## Acceptance criteria (from Jira)
"FAIL keeps previous knowledge published and marks QUARANTINED; WARN publishes with warning; state transitions tested."
1. FAIL keeps previous knowledge published and marks QUARANTINED -> scenario: failed-validation-quarantines
2. WARN publishes with warning -> scenario: warn-validation-publishes-with-warning
3. State transitions tested -> scenarios: pass-validation-publishes, gate-rejects-non-validating-state

## Affected
Capabilities: `spec/capabilities/harvest-validation.md` (modified — adds scenarios and a state-transition requirement).   Docs/contracts: none changed (gate matches the `PASS | WARN | FAIL` and `QUARANTINED`/`PUBLISHED` vocabulary already in `docs/HARVESTERS.md` and the Confluence Contracts; no new contract introduced).

## Risks and open questions
- No `harvest_runs` table exists yet, so this story cannot test an actual DB state transition — only the pure decision function and its in-memory state guard. This is flagged under "Not verified" at verification time.
- The real validator (which runs the 10 checks in `docs/HARVESTERS.md` section 5) is a separate, larger story; this gate accepts any object exposing a `status` of `PASS`/`WARN`/`FAIL` so it can be wired to that validator later without changes.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR.
