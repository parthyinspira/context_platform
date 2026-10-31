# Capability: source registry

### Requirement: Sources are rows
The system SHALL store every source as a row in `sources`, created only via `POST /sources` with valid `type`, `uri`, `schedule`, `credentials_ref`, `owner` and `sensitivity`; onboarding a new source SHALL NOT require a code change.
#### Scenario: register a source
- **Given** a valid type, uri, cron schedule, credentials_ref, owner and sensitivity
- **When** `POST /sources` is called
- **Then** a row is stored with status `active`, `source.registered` is published on the `EventBus`, and the row's id is returned

### Requirement: POST /sources validates input
The system SHALL reject `POST /sources` requests where `type`, `uri`, `schedule`, `credentials_ref`, `owner` or `sensitivity` are missing or malformed, before storing any row.

#### Scenario: reject invalid type
- **Given** a request body with an empty or missing `type`
- **When** `POST /sources` is called
- **Then** the response is `422` and no row is stored

#### Scenario: reject invalid uri
- **Given** a request body with an empty or missing `uri`
- **When** `POST /sources` is called
- **Then** the response is `422` and no row is stored

#### Scenario: reject invalid schedule
- **Given** a request body with a `schedule` that is not a valid 5-field cron expression
- **When** `POST /sources` is called
- **Then** the response is `422` and no row is stored

#### Scenario: reject missing credentials_ref
- **Given** a request body with an empty or missing `credentials_ref`
- **When** `POST /sources` is called
- **Then** the response is `422` and no row is stored

#### Scenario: reject missing owner
- **Given** a request body with an empty or missing `owner`
- **When** `POST /sources` is called
- **Then** the response is `422` and no row is stored

#### Scenario: reject invalid sensitivity
- **Given** a request body with a `sensitivity` value outside `{public, internal, confidential, restricted}`
- **When** `POST /sources` is called
- **Then** the response is `422` and no row is stored

### Requirement: Credentials are references
The system SHALL store only a `credentials_ref`; secret values SHALL NOT be stored, logged or returned. Resolving a `credentials_ref` into an actual secret value SHALL happen only through `SecretStore.get`, via `adapters.secret_store.resolve.resolve_credential`.

#### Scenario: read a source
- **Given** a source with a credentials_ref
- **When** it is fetched through the API
- **Then** no secret value appears in the response or logs

#### Scenario: resolve-credential-success
- **Given** a `credentials_ref` key that resolves to a value in the configured `SecretStore`
- **When** `resolve_credential(credentials_ref, secret_store)` is called
- **Then** it returns that value

#### Scenario: resolve-credential-missing-key
- **Given** a `credentials_ref` key that does not resolve in the configured `SecretStore`
- **When** `resolve_credential(credentials_ref, secret_store)` is called
- **Then** it raises `CredentialNotFoundError` whose message contains only the `credentials_ref` key, never a secret value

#### Scenario: api-never-logs-resolved-secret
- **Given** a `credentials_ref` that matches a real, resolvable secret value
- **When** a source is registered and served through the API
- **Then** the resolved secret value never appears in the HTTP request, the HTTP response, or any captured log line

### Requirement: Registration emits an event
The system SHALL publish `source.registered` through the `EventBus` when a source is created, and a consumer polling the same `EventBus` topic SHALL be able to receive that event.

#### Scenario: event on create
- **Given** a subscriber on `source.registered`
- **When** a source is created
- **Then** the subscriber receives the source id

#### Scenario: consumer-receives-source-registered
- **Given** a `POST /sources` request that will create a source, and an `EventBus` consumer polling the `source.registered` topic
- **When** the source is created and the consumer then polls `source.registered`
- **Then** the consumer receives exactly one event whose payload id matches the created source's id

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
