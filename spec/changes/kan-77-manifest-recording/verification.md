# Verification

Status: PASS
Date: 2026-10-31   Commit: review round 1 fixes on top of c26da59, branch kepler/kan-77-manifest-recording

## Checks
| Check | Result |
|---|---|
| Lint | PASS for this change: `ruff check harvesters --config pyproject.toml` -> "All checks passed!" (ruff 0.7.4). The full CI lint command `ruff check api scheduler adapters ontology harvesters` reports one I001 in `api/tests/test_source_registered_consumer.py:7`, a file this branch does not touch; the same error appears with this branch's changes stashed (unmodified main), so it predates this change and is left for its owner |
| Tests (full suite) | PASS: `python -m pytest harvesters/tests -q` 42 passed (30 original + 12 added in review round 1); `api/tests` 28 passed; `adapters/tests` 36 passed; `ontology/tests` 12 passed; `(cd scheduler && pytest)` 8 passed; `document_parsing/tests` 13 passed; `scripts/tests` 12 passed |
| docker compose up exercised | No service, Dockerfile or compose change in this story (pure library). `docker compose config -q` -> OK. End-to-end exercise of the module instead: `harvesters/tests/test_manifest.py::test_end_to_end_on_java_fixture` records a manifest over the real `fixtures/repos/java-sample` tree, saves it through `LocalObjectStore`, reloads it and reads it |
| contract-check | No mismatches. No schema change (no `migrations/` diff; manifest stored as JSON via `ObjectStore`). No ontology types touched. `Harvester` interface signatures in CLAUDE.md / `docs/HARVESTERS.md` unchanged; this story supplies the `manifest` that `validate(plan, manifest, results)` already names. No cloud SDK imports in `harvesters/` (`grep -rnE "google\.cloud|azure|boto3" harvesters` -> none). No MCP tools touched. `docs/HARVESTERS.md` rule 11 gained a note on the manifest format (review round 1); interface signatures unchanged |
| secret-scan | No real secrets. `git ls-files \| grep -E '\.env($\|\.)'` -> only `.env.example`. Pattern grep over added lines of `git diff origin/main...HEAD` matched only two clearly fake, commented values in `harvesters/tests/test_manifest.py` (a placeholder password inside a connection string and an `AKIAFAKE...` AWS-shaped key), seeded to prove redaction. Test output contains no secret values (the redaction tests assert the fake values are absent from stored reasons and from `to_json()`). Review round 1 added one more fake seeded password in `::test_loading_redacts_secrets_in_reasons` |
| Definition of Done | Met for a framework library story: AC evidenced by tests, tests added and passing, no contract change, no secrets, no cloud SDK outside `adapters/`. Reviewer verdict recorded in the PR |

```
$ python -m pytest harvesters/tests -q
..........................................                               [100%]
42 passed in 0.17s
```

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| Record every outcome with reason | `harvesters/tests/test_manifest.py::test_records_every_outcome_with_reason` (fetched, skipped, failed and discovered-only entries with discovery reason, outcome reason, size, timestamps), `::test_size_is_optional` | PASS |
| Reason required | `::test_discovered_requires_reason` (`""`, blank, `None`), `::test_outcome_requires_reason` (fetched/skipped/failed x empty/blank); manifest unchanged after each rejection; also `::test_ref_required`, `::test_negative_size_rejected` | PASS |
| Discover before outcome | `::test_outcome_requires_prior_discovery` (fetched/skipped/failed on an undiscovered ref raise `ManifestError` "not discovered") | PASS |
| One outcome per object | `::test_conflicting_outcome_rejected` (skipped then fetched rejected; skipped with a different reason rejected; original kept), `::test_identical_records_are_idempotent`, `::test_conflicting_rediscovery_rejected`, `::test_reloaded_manifest_keeps_rules` | PASS |
| Secret in a reason is redacted | `::test_secret_in_reason_is_redacted` (connection-string password replaced by `[REDACTED:...]`, absent from stored reason and from `to_json()`), `::test_secret_in_discovery_reason_is_redacted` | PASS |
| Validator reads outcomes and unaccounted objects | `::test_validator_reads_outcomes_counts_and_unaccounted` (`by_outcome`, `counts()` = discovered 5 / fetched 2 / skipped 1 / failed 1 / unaccounted 1, `unaccounted()`), `::test_entries_are_sorted_by_ref`, `::test_empty_manifest_counts`, `::test_end_to_end_on_java_fixture` (real fixture repo: every file discovered, `target/` skipped with reason, the rest fetched, unaccounted 0 after reload) | PASS |
| Manifest persisted and reloaded per run | `::test_manifest_persisted_and_reloaded` (key `manifests/<source_id>/<run_id>.json` via `LocalObjectStore`, loaded entries and counts equal), `::test_json_round_trip_is_stable`, `::test_store_rejects_unsafe_ids` (path-traversal ids rejected), `::test_store_load_forwards_clock` | PASS |
| Loaded manifest obeys the recording rules | `::test_loading_enforces_recording_rules` (7 cases: blank or missing discovery reason, missing or blank outcome reason, reason without outcome, empty ref, negative size), `::test_loading_rejects_duplicate_refs`, `::test_loading_redacts_secrets_in_reasons`, `::test_store_load_rejects_mismatched_ids` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Every discovered, fetched, skipped and failed object recorded with reason | Record every outcome with reason; Reason required; Discover before outcome; One outcome per object; Secret in a reason is redacted | PASS |
| Used by the validator | Validator reads outcomes and unaccounted objects; Manifest persisted and reloaded per run; Loaded manifest obeys the recording rules | PASS (read API and persistence the validator will call; the validator itself is KAN-83, see below) |

## Not verified
- Use by the real validator: the validator checks (KAN-83/KAN-84) and the `harvest_runs` table (KAN-75) do not exist on `main` yet. "Used by the validator" is evidenced by the read API, persistence and tests that consume them the way the validator will; integration is verified when KAN-83 lands.
- `docker compose up` was not run, because this story changes no service or container. `docker compose config -q` passed.
