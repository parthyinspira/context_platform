# KAN-65: Validation report screen (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-65   Branch: m8-ui-wizard-and-runs

## Scope
In: new `ValidationReport` screen/component, reachable from the run view's "View validation report" link (KAN-64), calling `GET /runs/{id}/validation` (KAN-58): overall PASS/WARN/FAIL `Badge`, a list of every check with its message, counts and sample failures, and a quarantine-explanation panel shown when the run's state is QUARANTINED.
Out: fixing the pre-existing gap where a real harvester run never populates per-check counts/samples (flagged in KAN-58's plan); this screen renders whatever shape the API returns, including a documented fallback when `report` is absent.

## Acceptance criteria (from Jira)
1. PASS/WARN/FAIL badge.
2. Every check with counts and samples.
3. Quarantine explanation.

## Requirements (at most 5)
- The screen SHALL fetch `GET /runs/{id}/validation` and `GET /runs/{id}` (for `state`), rendering an overall `Badge` showing the report's `status` (PASS/WARN/FAIL) with the existing variant mapping (success/warning/danger). (scenario: Given a report with status "FAIL", When the screen renders, Then the Badge shows the danger variant and "FAIL" text)
- The screen SHALL render one row per entry in the report's `checks` list, each showing its `name`, `message`, `counts` (as a key-value list) and `samples` (as a list, or "none" when empty). (scenario: Given a report with two checks, one with samples and one without, When rendered, Then both checks are listed with their counts, and the one with no samples shows "none" rather than an empty block)
- When the run's `state` is `QUARANTINED`, the screen SHALL show an explanation panel stating that previous knowledge remains published and this run's data was not applied, per `docs/UI_DESIGN.md` 4.5. (scenario: Given state QUARANTINED, When rendered, Then the quarantine explanation panel is shown; Given state PUBLISHED, Then it is not shown)
- When `GET /runs/{id}/validation` returns 404 (no `report` yet), the screen SHALL show an informative fallback using the run's `state` and `error` instead of a bare error screen. (scenario: Given a 404 from the validation endpoint and a run with `state=FAILED, error="connect failed: ..."`, When rendered, Then that state and error are shown as the fallback content, not a generic error state)

## Tasks
- [ ] 1. `ui/src/api.js`: add `getRunValidation(runId)` (tests: resolves with report shape, rejects/404 case surfaced distinctly)
- [ ] 2. `ui/src/components/ValidationReport.jsx`: overall Badge + per-check list (tests: badge variant per status, check rows with counts/samples, "none" for empty samples)
- [ ] 3. Quarantine explanation panel (tests: shown for QUARANTINED, hidden otherwise)
- [ ] 4. 404 fallback panel using run state/error (test: renders fallback content)

## Risks / not verifiable here
- Per KAN-58's plan: no harvester today populates `harvest_runs.report` with real counts/samples (the `Harvester.validate()` contract only returns `status`/`checks: dict[str,str]`/`errors`). This screen is verified against a seeded/mocked report payload; a live demo end-to-end report depends on a future story populating that column from a real validate() call.

## Approval
Approved by: parthasarathy.venkatachalam (user approved spec-batch), 2026-10-31
