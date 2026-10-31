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
The system SHALL store only a `credentials_ref`; secret values SHALL NOT be stored, logged or returned.
#### Scenario: read a source
- **Given** a source with a credentials_ref
- **When** it is fetched through the API
- **Then** no secret value appears in the response or logs

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
