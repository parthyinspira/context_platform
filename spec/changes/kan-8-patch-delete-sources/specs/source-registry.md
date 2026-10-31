# Delta for source registry

## ADDED Requirements

### Requirement: GET /sources lists all sources
The system SHALL expose `GET /sources` returning all rows in `sources`, with no secret values in the response.

#### Scenario: list-sources
- **Given** zero or more sources already registered
- **When** `GET /sources` is called
- **Then** the response is `200` with a list of all sources, each including `id`, `type`, `uri`, `schedule`, `credentials_ref`, `owner`, `sensitivity` and `status`, and no secret value beyond the stored `credentials_ref`

### Requirement: PATCH /sources/{id} updates schedule and status
The system SHALL expose `PATCH /sources/{id}` to update a source's `schedule` and/or `status`; `type`, `uri`, `credentials_ref`, `owner` and `sensitivity` SHALL NOT be changed through this endpoint. The system SHALL reject a malformed `schedule` or an unrecognized `status`, and SHALL return `404` for an unknown `id`.

#### Scenario: patch-schedule
- **Given** an existing source
- **When** `PATCH /sources/{id}` is called with a new valid cron `schedule`
- **Then** the response is `200`, the row's `schedule` is updated, and other fields are unchanged

#### Scenario: patch-status
- **Given** an existing source with status `active`
- **When** `PATCH /sources/{id}` is called with `status` set to `disabled`
- **Then** the response is `200` and the row's `status` is `disabled`

#### Scenario: patch-invalid-schedule
- **Given** an existing source
- **When** `PATCH /sources/{id}` is called with a `schedule` that is not a valid 5-field cron expression
- **Then** the response is `422` and the row is unchanged

#### Scenario: patch-invalid-status
- **Given** an existing source
- **When** `PATCH /sources/{id}` is called with a `status` outside `{active, disabled}`
- **Then** the response is `422` and the row is unchanged

#### Scenario: patch-unknown-source
- **Given** no source exists with a given `id`
- **When** `PATCH /sources/{id}` is called for that `id`
- **Then** the response is `404` and no row is stored or changed

### Requirement: DELETE /sources/{id} soft-deletes a source
The system SHALL expose `DELETE /sources/{id}` that sets the source's `status` to `disabled` without removing the row. The system SHALL return `404` for an unknown `id`.

#### Scenario: delete-soft-disables
- **Given** an existing source with status `active`
- **When** `DELETE /sources/{id}` is called
- **Then** the response is `200` (or `204`), the row still exists, and its `status` is `disabled`

#### Scenario: delete-unknown-source
- **Given** no source exists with a given `id`
- **When** `DELETE /sources/{id}` is called for that `id`
- **Then** the response is `404`
