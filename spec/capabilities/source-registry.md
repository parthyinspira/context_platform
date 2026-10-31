# Capability: source registry

### Requirement: Sources are rows
The system SHALL store every source as a row in `sources`; onboarding a new source SHALL NOT require a code change.
#### Scenario: register a source
- **Given** a valid type, uri, schedule and credentials_ref
- **When** `POST /sources` is called
- **Then** a row is stored with status `active` and its id is returned

### Requirement: Credentials are references
The system SHALL store only a `credentials_ref`; secret values SHALL NOT be stored, logged or returned.
#### Scenario: read a source
- **Given** a source with a credentials_ref
- **When** it is fetched through the API
- **Then** no secret value appears in the response or logs

### Requirement: Registration emits an event
The system SHALL publish `source.registered` through the `EventBus` when a source is created.
#### Scenario: event on create
- **Given** a subscriber on `source.registered`
- **When** a source is created
- **Then** the subscriber receives the source id
