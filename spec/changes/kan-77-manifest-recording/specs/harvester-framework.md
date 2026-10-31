# Delta for harvester-framework

## ADDED Requirements
### Requirement: Manifest recording
Every harvest run SHALL record each object it discovered, fetched, skipped or failed in a run manifest, each record with a non-empty reason, and the manifest SHALL be persisted per run so the validator can read it.

#### Scenario: record every outcome with reason
- **Given** a manifest for a source and run
- **When** objects are recorded as discovered, then fetched, skipped or failed, each with a reason
- **Then** the manifest holds one entry per object with its outcome, its discovery reason, its outcome reason, and size when known

#### Scenario: reason required
- **Given** a manifest
- **When** any object is recorded with an empty or blank reason
- **Then** the record is rejected and the manifest is unchanged

#### Scenario: discover before outcome
- **Given** a manifest where object `a.sql` was never discovered
- **When** `a.sql` is recorded as fetched, skipped or failed
- **Then** the record is rejected

#### Scenario: one outcome per object
- **Given** an object already recorded as skipped
- **When** it is recorded again as fetched
- **Then** the record is rejected; recording the identical skipped record again is accepted as a no-op

#### Scenario: secret in a reason is redacted
- **Given** a fetch failure whose reason text contains a connection string with a password
- **When** it is recorded as failed
- **Then** the stored reason contains a redaction marker and never the password

#### Scenario: validator reads outcomes and unaccounted objects
- **Given** a manifest with discovered objects, some fetched, some skipped, some failed and some with no outcome
- **When** the validator reads it
- **Then** it gets the entries per outcome with reasons, counts per outcome, and the list of discovered objects with no outcome

#### Scenario: manifest persisted and reloaded per run
- **Given** a recorded manifest for source `S` and run `R`
- **When** it is saved through the `ObjectStore` and loaded again by `S` and `R`
- **Then** the loaded manifest is equal to the saved one, stored at key `manifests/S/R.json`
