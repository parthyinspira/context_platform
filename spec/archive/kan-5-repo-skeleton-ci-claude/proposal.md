# KAN-5: Repo skeleton, CI and CLAUDE.md

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-5   Epic: 1 Foundation   Branch: kepler/kan-5-repo-skeleton-ci-claude

## Why
KAN-101 built the compose skeleton and KAN-102 added the adapter interfaces, but neither added a CI pipeline: there is no `.github/workflows/`, and KAN-101's `verification.md` explicitly deferred its Linux leg "to a CI job on `ubuntu-latest` to be added in KAN-5". Without CI, lint/test regressions and the undone Linux `docker compose up` check can land on `main` unnoticed. `CLAUDE.md` already exists and documents architecture, ontology v0 and the harvester interface (added before KAN-101/102); this story confirms it still matches the current repo and closes the CI gap.

## What changes
- Add `.github/workflows/ci.yml` running on push/PR to `main`:
  - Python lint (`ruff`) across `api/`, `scheduler/`, `adapters/`.
  - Python tests (`pytest`) for `api/tests`, `scheduler/tests`, `adapters/tests`.
  - UI tests (`node --test`) for `ui/test`.
  - A `docker compose up` smoke test on `ubuntu-latest` that waits for all services healthy and checks each `/health` endpoint, then `docker compose down -v` — this closes the KAN-101 "Linux not verified" gap.
- Add a minimal `ruff` config (`pyproject.toml`) so lint has defined rules instead of defaults drifting.
- Verify `CLAUDE.md` still documents architecture, ontology v0 and the harvester interface against the current repo (no drift found expected; fix only if found).

## In scope
- One CI workflow file with lint, unit test and compose-smoke-test jobs.
- `pyproject.toml` ruff config shared by `api`, `scheduler`, `adapters`.
- `requirements-dev.txt` updates to add `ruff` where Python tests run.
- Confirming/fixing `CLAUDE.md` accuracy for architecture, ontology v0, harvester interface.

## Out of scope
- Any new business logic (source registry, harvesters, ontology updater, MCP).
- Cloud CI deploy steps (GCP/Azure) — local CI only, per Epic 1 scope.
- Branch protection / required-checks configuration in GitHub repo settings (outside repo code, not requested by the AC).
- Windows CI runner — AC and KAN-101 gap are specifically about the Linux leg; Windows was already verified locally in KAN-101.

## Acceptance criteria (from Jira)
"repo has lint/test CI; CLAUDE.md documents architecture, ontology v0 and harvester interface."
1. Repo has lint CI -> scenario: ci-lint-runs
2. Repo has test CI -> scenario: ci-test-runs
3. CLAUDE.md documents architecture, ontology v0, harvester interface -> scenario: claude-md-documents-contracts

## Affected
Capabilities: `spec/capabilities/foundation.md` (CI requirement added)   Docs/contracts: no schema/ontology/harvester interface contract change, so no Confluence Contracts update needed.

## Risks and open questions
- GitHub Actions minutes/availability were not exercised in this sandboxed session (no outbound push performed until PR stage); the workflow YAML is validated locally for syntax/shape and by running each of its steps directly, but actual Actions-runner execution can only be confirmed once the PR is open and CI runs there.

## Approval
Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
