# KAN-8: GET/PATCH/DELETE /sources

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-8   Epic: KAN-6 Epic 2: Source registry and API   Branch: kan-8-patch-delete-sources

## Why
`POST /sources` (KAN-7) lets operators register sources but there is no way to list what is registered, change a source's schedule or status, or retire a source. Onboarding/operating sources end-to-end needs read, update and soft-delete.

## What changes
- `GET /sources` lists all sources (no secret values in the response, matching the existing `credentials_ref`-only contract).
- `PATCH /sources/{id}` updates `schedule` and/or `status` on an existing source; other fields are immutable through this endpoint.
- `DELETE /sources/{id}` soft-deletes a source by setting `status=disabled`; it does not remove the row.
- 404 responses for an unknown `id` on `PATCH`/`DELETE`.
- 422 for an invalid `schedule` (bad cron) or `status` on `PATCH`.

## In scope
- `GET /sources` (list, no filtering/pagination — hackathon scope).
- `PATCH /sources/{id}` for `schedule` and `status` only.
- `DELETE /sources/{id}` as a soft delete (`status=disabled`), not a row delete.
- Input validation and 404/422 handling consistent with `POST /sources`.

## Out of scope
- Filtering, sorting or pagination on `GET /sources`.
- Updating `type`, `uri`, `credentials_ref`, `owner` or `sensitivity` via `PATCH`.
- Hard delete / row removal.
- Re-enabling a disabled source via a dedicated endpoint (covered by the same `PATCH status` path, no new endpoint needed).

## Acceptance criteria (from Jira)
1. List sources -> scenarios: list-sources
2. Update schedule/status -> scenarios: patch-schedule, patch-status, patch-invalid-schedule, patch-invalid-status, patch-unknown-source
3. Soft delete (status=disabled) -> scenarios: delete-soft-disables, delete-unknown-source

## Affected
Capabilities: spec/capabilities/source-registry.md   Docs/contracts: none (no schema or ontology change; `status` already exists on `sources` per CLAUDE.md's Postgres schema v0)

## Risks and open questions
- None identified; this extends the existing `api/app/main.py` routes and `app/schemas.py` models already used by `POST /sources`.

## Changes during development
(none)

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
