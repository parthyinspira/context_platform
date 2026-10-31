# Verification

Status: PASS
Date: 2026-10-31   Commit: 6800b9ed0be6a8c95ecd674b70666c069885cedc (pre-commit; see PR for final sha)

## Fix found during verification
Running the image live against a seeded Postgres row (`docker compose run --rm harvester` with a
`source.type` that has no registered harvester) raised `UnknownSourceTypeError` uncaught past
`main()`'s `except RunnerError` handler, producing a Python traceback and exit code `1` instead of
the documented clean-abort contract (one-line message, exit `2`, no `harvest_runs` write). Fixed in
`harvesters/run.py::run()` by wrapping the `get_harvester()` lookup and re-raising as `RunnerError`;
added `harvesters/tests/test_run.py::test_runner_rejects_unregistered_source_type` and re-verified
live (see Checks above): both the unregistered-type and unknown-`plan_id` cases now exit `2` with a
clean message.

## Checks
| Check | Result |
|---|---|
| Lint (`python -m ruff check harvesters --config pyproject.toml`) | PASS |
| Lint, full matrix (`python -m ruff check api scheduler adapters ontology harvesters harvest_validation --config pyproject.toml`) | 1 pre-existing finding in `api/tests/test_source_registered_consumer.py` (import order), unrelated to this change and already flagged as a pre-existing gap in `spec/archive/kan-85-publish-quarantine-gate/verification.md`; no finding in any file this story touched |
| Tests (`python -m pytest harvesters/tests -q`) | PASS - 81 passed (72 pre-existing + 9 new in `test_run.py`) |
| Other package suites unaffected (`api`, `scheduler`, `adapters`, `ontology`, `harvest_validation`) | PASS - 28, 8, 36, 12, 68 passed respectively, run individually matching CI's per-package invocation |
| `docker compose config` validates the new `harvester` service | PASS - `docker compose config --services` (no profile) does NOT list `harvester`, confirming it is excluded from the default `docker compose up` set used by the CI `compose-smoke-test` job; `docker compose --profile harvester config --services` does list it |
| Image builds (`docker compose --profile harvester build harvester`) | PASS |
| Live run against real Postgres (`docker compose run --rm -e SOURCE_ID=... -e PLAN_ID=... harvester` with a seeded `sources`/`harvest_runs` row) | PASS - container reads `SOURCE_ID`/`PLAN_ID` from the environment, connects to the compose `postgres` service over `DATABASE_URL`, loads the row, and aborts cleanly with exit code `2` and a one-line message (no traceback) for both an unregistered source type (`git`, expected - no real harvester is registered yet, see scope) and an unknown `plan_id`; found and fixed a real bug this way (see below) |
| contract-check | No mismatches: no schema/migration, ontology, or harvester-interface change (the `Harvester` ABC is untouched, only driven); no cloud SDK import (`google.cloud`/`boto3`/`azure.*`) anywhere in `harvesters/run.py`, `harvesters/Dockerfile` or `docker-compose.yml`; `docs/HARVESTERS.md` updated with the new runner's env-var contract |
| secret-scan | No secrets found in the diff (`harvesters/run.py`, `harvesters/Dockerfile`, `harvesters/tests/*`, `docker-compose.yml`, `docs/HARVESTERS.md`); `.env` untracked, only `.env.example` tracked |
| Definition of Done | Code + tests + spec delta + docs done |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command) | Result |
|---|---|---|
| runner-reads-source-id-and-plan-id-from-env-or-cli | `harvesters/tests/test_run.py::test_parse_args_reads_from_environment`, `::test_parse_args_cli_flags_override_environment`, `::test_parse_args_requires_source_id_and_plan_id` | PASS |
| runner-drives-full-lifecycle-to-published | `harvesters/tests/test_run.py::test_runner_drives_full_lifecycle_to_published` | PASS |
| runner-quarantines-on-failed-validation | `harvesters/tests/test_run.py::test_runner_quarantines_on_failed_validation` | PASS |
| runner-fails-cleanly-on-connect-error | `harvesters/tests/test_run.py::test_runner_fails_cleanly_on_connect_error` | PASS |
| runner-rejects-unknown-plan-id | `harvesters/tests/test_run.py::test_runner_rejects_unknown_plan_id`, `::test_runner_rejects_plan_id_belonging_to_a_different_source` | PASS |
| runner-is-platform-portable | Manual inspection of `harvesters/Dockerfile` (`ENTRYPOINT ["python", "-m", "harvesters.run"]`, no positional args, env-var config) and `harvesters/run.py` (no cloud SDK import); `grep -rn "google.cloud\|boto3\|azure\." harvesters/run.py harvesters/Dockerfile docker-compose.yml` returns nothing; `docker compose config --services` includes `harvester` | PASS for the image/entrypoint portability; see "Not verified" below for the live-platform half |
| `main()` exit codes (0 published/quarantined, 1 failed, 2 aborted) | `harvesters/tests/test_run.py::test_main_exits_zero_on_published`, `::test_main_exits_nonzero_on_failed`, `::test_main_exits_two_on_runner_error` | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Harvester image takes `source_id` and `plan id` | runner-reads-source-id-and-plan-id-from-env-or-cli | PASS - env vars `SOURCE_ID`/`PLAN_ID` read by default, `--source-id`/`--plan-id` CLI flags override |
| Runs the lifecycle end to end | runner-drives-full-lifecycle-to-published, runner-quarantines-on-failed-validation, runner-fails-cleanly-on-connect-error | PASS - connect/discover/harvest/normalize/validate all invoked through the real `Harvester` ABC and `harvest_validation.PublishQuarantineGate`; verified for the publish, quarantine and connect-failure paths |
| Writes `harvest_runs` state | all of the above, plus runner-rejects-unknown-plan-id | PASS - `conn.state_history` asserted as `["HARVESTING", "VALIDATING", "PUBLISHED"\|"QUARANTINED"]` or `["HARVESTING", "FAILED"]`; no write at all for an unknown/mismatched plan id |
| Publishes `harvest.completed` | runner-drives-full-lifecycle-to-published, runner-quarantines-on-failed-validation, runner-fails-cleanly-on-connect-error | PASS - fake `EventBus.published` asserted with topic, run id, source id, final state, `published`/`warning` flags and record counts for all three terminal outcomes |
| The same image works under compose, Cloud Run Jobs and Container Apps Jobs | runner-is-platform-portable | PARTIAL - the image/entrypoint is verified platform-neutral (env-var-only config, no cloud SDK import, no positional CLI args) and `docker compose run harvester` is wired; actually executing it as a live GCP Cloud Run Job or Azure Container Apps Job is **not verified** (see below) |

## Not verified
- Running the built image as a live GCP Cloud Run Job or Azure Container Apps Job: this hackathon/dev environment has no provisioned Cloud Run or Container Apps account to execute against, and provisioning one is explicitly out of scope for this story (see proposal.md "Out of scope"). What is verified: the image has no platform-specific `ENTRYPOINT`/`CMD` arguments, takes all configuration from environment variables (the mechanism both Cloud Run Jobs and Container Apps Jobs use to pass per-execution config), and contains no cloud-provider SDK import anywhere under `harvesters/`.
- The runner's unit tests use the in-memory `FakePostgresConnection` fixture (`harvesters/tests/fake_postgres.py`), matching the existing pattern in `adapters/tests/contract/fake_postgres.py`; `docker compose run --rm harvester` against a real Postgres container was additionally exercised live during verification (see Checks above) for the two abort paths, since no real harvester type is registered yet to exercise the full publish/quarantine paths live.
- Entity/Edge/Chunk persistence to `entities`/`edges`/`chunks` is explicitly out of scope (the future normalizer's job, per `CLAUDE.md`'s flow) and is not exercised beyond counting records in the `harvest.completed` payload.
- No real (non-fixture) harvester type is registered yet for any source (git/document harvesters are separate, later stories); the runner is exercised against test-only fixture harvesters registered in `harvesters/tests/test_run.py`, the same pattern `harvesters/tests/test_registry.py` already uses for the registry itself.
