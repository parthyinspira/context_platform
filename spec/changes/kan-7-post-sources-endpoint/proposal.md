# KAN-7: POST /sources endpoint

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-7   Epic: KAN-2 Source registry/API   Branch: kepler/kan-7-post-sources-endpoint

## Why
The `sources` table exists (KAN-4) but nothing can write to it yet. CLAUDE.md requires that onboarding a new source is "a row, never a code change" — that requires an API to create the row. This story adds the `POST /sources` endpoint so a source can be registered through the API, which every later harvester/scheduler story depends on.

## What changes
- Add `POST /sources` to the `api` FastAPI app.
- Validate `type`, `uri`, `schedule` (must be a valid cron expression), `credentials_ref`, `owner`, `sensitivity` on the request body.
- On success, insert a row into `sources` with `status='active'`, and return the created id (and the stored row, excluding any secret value — only `credentials_ref`, the reference key, is ever stored/returned).
- Publish `source.registered` on the `EventBus` (already required by `spec/capabilities/source-registry.md`) when a source is created.

## In scope
- The `POST /sources` endpoint: request validation, insert, response.
- Wiring the `api` service to Postgres (`DATABASE_URL`) and to the `EventBus` adapter via `adapters/factory.py`.
- Unit tests for validation failures and the success path.

## Out of scope
- `GET /sources`, `PATCH`/`DELETE`, listing or scheduling endpoints (future stories).
- Harvester execution, dispatcher/scheduler logic.
- Idempotency / upsert-by-external-id semantics (that applies to harvester-written entities, not this registration endpoint).
- Resolving `credentials_ref` through `SecretStore` (that happens when a harvester runs, not at registration).

## Acceptance criteria (from Jira)
1. Validates `type`, `uri`, `schedule` (cron), `credentials_ref`, `owner`, `sensitivity` -> scenarios: reject invalid type, reject invalid uri, reject invalid schedule, reject missing credentials_ref, reject missing owner, reject invalid sensitivity
2. Stores row with `status=active` and returns `id` -> scenarios: register a source

## Affected
Capabilities: spec/capabilities/source-registry.md (adds request-validation requirement)   Docs/contracts: none (no schema or ontology change; `sources` columns already match CLAUDE.md)

## Risks and open questions
- Cron validation library: using a small hand-rolled 5-field cron syntax check (no new heavy dependency), consistent with "small modules" convention. Flagging as the lightest option that still rejects obviously malformed schedules.
- `type` and `sensitivity` are constrained to the small enumerations already implied by CLAUDE.md (ontology entity source types are open-ended per `docs/HARVESTERS.md`, but `sensitivity` has an established default of `internal`; proposal uses `{public, internal, confidential, restricted}` and flags this as the full sensitivity enum used elsewhere in the repo — none found, so this is a new but reasonable closed set for a hackathon). This is not a schema/ontology change — `sensitivity` stays `TEXT` in Postgres; this is request-level validation only.

## Changes during development
(none)

## Approved by: auto (user started spec-auto), 2026-10-30; human review at PR
