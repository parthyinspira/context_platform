# KAN-43: Demo script and sample sources (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-43   Branch: kepler/kan-43-demo-script-sample-sources

## Scope
In: demo shell script; fixture completeness check; non-sensitive verification; demo README
Out: actual harvester runs (covered by other stories), production data, UI automation

## Acceptance criteria (from Jira)
1. Non-sensitive sample repos and docs in fixtures/
2. Script rehearsed end to end

## Requirements (only new or changed behaviour; at most 5)
- The project SHALL provide a `demo/demo.sh` script that walks through the 4 CLAUDE.md demo steps with curl commands and human-readable output.
- The project SHALL provide a `demo/README.md` explaining prerequisites, what each step does, and expected output.
- The script SHALL use only the local fixture sources (no external repos, no production data).

## Tasks
- [x] 1. Write demo/demo.sh (curl commands for each demo step)
- [x] 2. Write demo/README.md (prerequisites and expected output)
- [x] 3. Verify fixtures are non-sensitive (no real secrets, no production data)
- [x] 4. Write tests for fixture content validation
- [x] 5. Write verification.md

## Risks / not verifiable here
- End-to-end run requires docker compose stack running (not run in CI for this story; covered by KAN-101 compose tests).

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
