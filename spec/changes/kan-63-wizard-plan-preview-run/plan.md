# KAN-63: Add-source wizard: harvest plan preview and run (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-63   Branch: m8-ui-wizard-and-runs

## Scope
In: wizard step 4 ("Plan"), a new `PlanSummaryCard` component showing what will be pulled/skipped by type and size, estimated bytes/files/time/tokens, budget-warning callouts, and a minimal editable rule (an `include`/`exclude` glob-pattern text list the user can edit before running); a "Run now" action on step 5 that calls `POST /sources/{id}/runs` (KAN-58) and navigates to the run view (KAN-64).
Out: a full rules editor UI (drag/drop, per-node overrides) — minimal is an editable text list of glob patterns, pre-filled from the plan's `include`/`exclude`; scheduling a recurring harvest (source `schedule` field already exists from B2, not re-exposed here).

## Acceptance criteria (from Jira)
1. Shows what will be pulled and skipped by type and size.
2. Estimates for bytes/files/time/tokens.
3. Budget warnings.
4. Editable rules.
5. Run now.

## Requirements (at most 5)
- Step 4 SHALL call `POST /sources/{id}/plan` with the step-3 selection and render a `PlanSummaryCard` showing pulled vs. skipped counts/bytes grouped by detected stack/type (from `Profile.counts_by_type`/`detected_stacks`) and the plan's `include`/`exclude` patterns. (scenario: Given a plan response with counts_by_type and an exclude pattern, When step 4 renders, Then pulled/skipped groups and the exclude pattern are shown)
- The card SHALL show the plan response's byte/file/time/token estimates as labelled values. (scenario: Given a plan response with estimated bytes, files, time and tokens, When rendered, Then all four values are shown with labels)
- When the plan response includes `budget_warnings`, the card SHALL render each as a visible warning (icon + text, not colour alone), using the existing `ErrorBanner`/`Badge` visual language. (scenario: Given a non-empty `budget_warnings` list, When rendered, Then a warning is shown per entry; Given an empty list, Then no warning is shown)
- The `include`/`exclude` patterns SHALL be editable as a text list before running; edits SHALL be sent back in the `POST /sources/{id}/runs` plan body rather than the original unedited plan. (scenario: Given the user adds an exclude pattern, When "Run now" is activated, Then the run-creation request body's plan includes the edited pattern)
- Step 5's "Run now" action SHALL call `POST /sources/{id}/runs` with the (possibly edited) plan and, on success, navigate to the run view with the returned run id. (scenario: Given a valid plan, When "Run now" is activated and the API returns a run id, Then the app navigates to the run view for that id; Given the API call fails, Then an error is shown and the wizard stays on step 5)

## Tasks
- [ ] 1. `ui/src/api.js`: add `planSource(sourceId, selection)` and `createRun(sourceId, plan)` (tests: resolve with plan/run shapes)
- [ ] 2. `ui/src/components/PlanSummaryCard.jsx` (tests: pulled/skipped groups, estimates, budget warnings rendered/absent)
- [ ] 3. Editable include/exclude text-list control wired into wizard state (test: edited pattern appears in the run-creation call body)
- [ ] 4. Step 5 "Run now" wiring + navigation to run view (tests: success navigates, failure shows error and stays)

## Risks / not verifiable here
-

## Approval
Approved by: parthasarathy.venkatachalam (user approved spec-batch), 2026-10-31
