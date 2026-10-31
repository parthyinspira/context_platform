# Stage 3: Verify

**Purpose:** prove the change meets the spec before a PR exists.
**Who:** dev agent (a separate session is preferred). **Inputs:** change folder, code.

## Steps
1. Run lint and the full test suite. Never skip or weaken a test to pass.
2. Run `docker compose up` (or the affected services) and exercise the change end to end.
3. For every scenario in the deltas, record evidence in `verification.md`: test name, command output, or screenshot, with result PASS or FAIL.
4. Map every Jira acceptance criterion to its scenarios; none may be unevidenced.
5. Run the `contract-check` skill: schema vs migrations, ontology, harvester interface, adapter imports, secrets, docs.
6. Check the Definition of Done in `docs/DEV_WORKFLOW.md`.
7. Run `python scripts/spec_check.py spec/changes/kan-<n>-<slug>` (also checks tasks are ticked and `verification.md` is complete).
8. Write the overall status at the top of `verification.md`: PASS, or FAIL with reasons. On FAIL return to stage 2.

## Exit criteria (gate 3)
Status PASS, every scenario evidenced, `contract-check` clean, `spec_check` passes.

## Failure handling
Do not open a PR with a FAIL. If a scenario cannot be verified (for example needs a cloud resource), say so explicitly in `verification.md` as "NOT VERIFIED" with the reason; the user decides whether to proceed.
