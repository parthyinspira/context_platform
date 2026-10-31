# KAN-9: Publish source.registered through the EventBus

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-9   Epic: 2 Source registry   Branch: kan-9-publish-source-registered-through

## Why
Downstream work (harvester dispatch, scheduling) needs to react to a new source without polling the `sources` table. `POST /sources` must publish `source.registered` through the cloud-neutral `EventBus` interface so a consumer can pick it up the same way regardless of which `EventBus` adapter is deployed.

## Current state
Both pieces already exist in `main`:
- `api/app/main.py` publishes `source.registered` with `{"id": source_id}` on the same connection/transaction as the `sources` insert, via the injected `EventBus` (`event_bus_dependency`), built from `adapters.event_bus.postgres_outbox.PostgresOutboxEventBus` (the default `EVENT_BUS=postgres_outbox` adapter per `spec/capabilities/foundation.md`).
- `adapters/event_bus/postgres_outbox.py` implements `publish`/`poll` against the `outbox_events` table, with its own contract tests (`adapters/tests/contract/test_event_bus.py`).
- `api/tests/test_sources.py::test_register_a_source_stores_active_row_and_returns_id` asserts the API calls `event_bus.publish("source.registered", {"id": ...})`, but against a `FakeEventBus` that only records calls — it does not exercise the outbox or a consumer actually reading the event back.

## Gap against the AC
The Jira AC requires "a consumer test included". No existing test drives the flow a consumer actually sees: create a source through the API, then have a separate consumer `poll("source.registered", ...)` the same outbox-backed `EventBus` and receive the id. This story adds exactly that test (and a thin seam to run it without a live Postgres), with no production code change expected since the publish wiring is already correct.

## What changes
- Add an integration-style consumer test that: builds a `PostgresOutboxEventBus` over a fake DB-API connection shared with the API's `connection_factory_dependency`/`event_bus_dependency` overrides, calls `POST /sources`, then calls `poll("source.registered", ...)` on that same bus and asserts the consumer receives the created source's id exactly once.
- No schema, ontology, or harvester-interface changes. Pub/Sub and Service Bus `EventBus` adapters remain explicitly out of scope ("later" per the AC).

## In scope
- A consumer-side test proving `source.registered` round-trips through the `EventBus` interface end to end from `POST /sources`.
- Minor test-seam additions only if needed to share a fake connection between the API test client and a standalone `PostgresOutboxEventBus` instance.

## Out of scope
- Pub/Sub and Azure Service Bus `EventBus` adapters (explicitly deferred by the AC).
- Any change to the `outbox_events` schema or migrations (already shipped in KAN-101/foundation).
- Any change to `POST /sources` validation behavior (covered by `spec/capabilities/source-registry.md`).

## Acceptance criteria (from Jira)
1. Creating a source publishes `source.registered` via the `EventBus` interface (Postgres outbox by default) -> scenario: source-registered-published-on-create (already covered by existing unit test)
2. Consumer test included -> scenario: consumer-receives-source-registered (new)

## Affected
Capabilities: `spec/capabilities/source-registry.md` (clarify the existing "Registration emits an event" requirement with an explicit consumer-delivery scenario)   Docs/contracts: none (no schema/ontology/harvester-interface change); no Confluence Contracts update needed.

## Risks and open questions
- No live Postgres is available in this environment (consistent with KAN-101/foundation verification); the consumer test uses the same in-memory fake DB-API connection pattern already used by `adapters/tests/contract/fake_postgres.py` and `api/tests/test_sources.py`, shared between the API call and the consumer's `poll`, so it is an integration test of the interface contract, not of a live outbox table.

## Approval
Approved by: auto (user started spec-auto), 2026-10-30
