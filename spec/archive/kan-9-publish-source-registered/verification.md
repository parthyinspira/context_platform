# Verification

Status: PASS
Date: 2026-10-30   Commit: 2e85cf38140ee68c34dc379958fd84b0859f5341 (+ this change's uncommitted diff)

## Checks
| Check | Result |
|---|---|
| Lint | No linter configured in the repo (no `ruff`/`eslint` config); none run, consistent with prior changes |
| Tests (api) | `python -m pytest api/tests -q` -> 18/18 passed, including the new consumer test |
| Tests (adapters) | `python -m pytest adapters/tests -q` -> 14/14 passed (unchanged) |
| contract-check | No schema, ontology, harvester-interface, adapter, or MCP changes in the diff (only a new test file + spec change folder); no cloud SDK imports found outside `adapters/` | PASS |
| secret-scan | No secrets found in diff or fixtures; `git ls-files` shows only `.env.example` tracked, no `.env` | PASS |
| `spec_check.py` (plan stage) | `python scripts/spec_check.py spec/changes/kan-9-publish-source-registered` -> OK | PASS |

## Scenario evidence
| Requirement / Scenario | Evidence (test, command, result) | Result |
|---|---|---|
| Registration emits an event / event on create | `api/tests/test_sources.py::test_register_a_source_stores_active_row_and_returns_id` asserts `bus.published == [("source.registered", {"id": body["id"]})]` against a `FakeEventBus` | PASS |
| Registration emits an event / consumer-receives-source-registered | `api/tests/test_source_registered_consumer.py::test_consumer_receives_source_registered_event`: `POST /sources` through the API with `event_bus_dependency` overridden to a real `PostgresOutboxEventBus` over a shared `FakePostgresConnection` (the same fake used by `adapters/tests/contract/test_event_bus.py`), then `event_bus.poll("source.registered", limit=10)` on that same bus returns exactly one event whose `payload == {"id": source_id}`, and a second poll returns `[]` (delivered-once) | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Creating a source publishes `source.registered` via the `EventBus` interface (Postgres outbox by default) | event on create | PASS (pre-existing, re-verified) |
| Consumer test included | consumer-receives-source-registered | PASS (new) |

## Not verified
- No live Postgres is available in this environment; the consumer test exercises the `EventBus`/outbox contract against the same in-memory fake DB-API connection pattern used by the adapter's own contract tests (`adapters/tests/contract/fake_postgres.py`), not a real `outbox_events` table. This mirrors the gap already recorded in KAN-101/foundation verification and is not new to this change.
- Pub/Sub and Azure Service Bus `EventBus` adapters are explicitly out of scope per the Jira AC ("later") and are not implemented or tested here.
