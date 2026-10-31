# Verification

Status: PASS
Date: 2026-10-30   Commit: e0e3815 (pre-commit working tree; see PR commit for final SHA)

## Checks
| Check | Result |
|---|---|
| Lint | PASS — `ruff check api scheduler adapters --config pyproject.toml`: All checks passed |
| Tests (full suite) | PASS — `python -m pytest api/tests -q`: 17 passed (also re-ran as `cd api && python -m pytest tests -q`: 17 passed, matching both CI invocation styles); `python -m pytest adapters -q`: 9 passed, unaffected |
| docker compose up exercised | PASS — `docker compose up -d --build postgres migrate api`: postgres healthy, migrate exited 0, api healthy; live `POST /sources` and `GET /health` both exercised against the real container (see scenario evidence below); torn down with `docker compose down -v` |
| contract-check | No mismatches: no schema/ontology/harvester/MCP contract touched (sources table and columns unchanged from KAN-4); no cloud SDK imports outside `adapters/`; `.env` untracked, only `.env.example` tracked |
| secret-scan | No secrets found in diff or logs; grepped `api/app`, `api/tests`, `api/Dockerfile`, `api/requirements.txt`, `docker-compose.yml` for key/token/password patterns — none found; live container logs grepped for the test `credentials_ref` value — not present (only the reference key is ever stored/returned, never a secret value) |
| Definition of Done | Met: AC demonstrable end-to-end against a live Postgres container, tests added and passing, runs from `docker compose up`, no contract changes needed, no secrets/cloud SDK violations |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, screenshot) | Result |
|---|---|---|
| POST /sources validates input / reject invalid type | `api/tests/test_sources.py::test_reject_blank_required_fields[type-]` — PASS | PASS |
| POST /sources validates input / reject invalid uri | `api/tests/test_sources.py::test_reject_blank_required_fields[uri-]` — PASS | PASS |
| POST /sources validates input / reject invalid schedule | `api/tests/test_sources.py::test_reject_invalid_schedule` (5 cases incl. empty, malformed, wrong field count) — PASS. Live: `curl -X POST .../sources -d '{"schedule":"bad",...}'` returned `422` | PASS |
| POST /sources validates input / reject missing credentials_ref | `api/tests/test_sources.py::test_reject_blank_required_fields[credentials_ref-]` — PASS | PASS |
| POST /sources validates input / reject missing owner | `api/tests/test_sources.py::test_reject_blank_required_fields[owner-]`, `test_reject_missing_field` — PASS | PASS |
| POST /sources validates input / reject invalid sensitivity | `api/tests/test_sources.py::test_reject_invalid_sensitivity` — PASS. Live: `curl` with `"sensitivity":"top-secret"` returned `422` | PASS |
| Sources are rows / register a source | `api/tests/test_sources.py::test_register_a_source_stores_active_row_and_returns_id` and `test_accepts_valid_cron_schedules` (4 cron shapes) — PASS. Live: `curl -X POST .../sources` with a valid body returned `201` with `status:"active"` and an `id`; `psql -c "select id, type, status, credentials_ref, sensitivity from sources"` showed the row with `status=active`; `psql -c "select topic, payload from outbox_events"` showed `source.registered` published with the new id | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Validates type, uri, schedule (cron), credentials_ref, owner, sensitivity | reject invalid type/uri/schedule/credentials_ref/owner/sensitivity | PASS |
| Stores row with status=active; returns id | register a source | PASS |

## Not verified
(none — validation, storage, event publication and secret non-leakage were all verified both via mocked unit tests and a live `docker compose` Postgres run, not just fabricated)
