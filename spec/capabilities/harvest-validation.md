# Capability: harvest validation

### Requirement: Validation gates publishing
The system SHALL run the validator after harvest and SHALL publish knowledge only when status is PASS or WARN. The decision SHALL be made by a `PublishQuarantineGate` that only acts on a run in the `VALIDATING` state.
#### Scenario: failed validation
- **Given** a run whose validator status is FAIL
- **When** the gate evaluates
- **Then** the run is QUARANTINED and previously published knowledge is unchanged

#### Scenario: warn validation publishes with warning
- **Given** a run in state VALIDATING whose validator status is WARN
- **When** the gate evaluates
- **Then** the run transitions to PUBLISHED, knowledge is published, and the result is flagged as a warning

#### Scenario: pass validation publishes
- **Given** a run in state VALIDATING whose validator status is PASS
- **When** the gate evaluates
- **Then** the run transitions to PUBLISHED, knowledge is published, and the result carries no warning

#### Scenario: gate rejects non-validating state
- **Given** a run that is not in state VALIDATING (for example HARVESTING)
- **When** the gate is asked to evaluate it
- **Then** the gate raises an error and no state transition occurs

### Requirement: Standard checks
The validator SHALL check completeness, exclusion integrity, budget compliance, parse success, expected yield, ontology conformance, referential integrity, delete sanity, secrets/PII and freshness.
#### Scenario: excluded type fetched
- **Given** a manifest containing a file type the plan excluded
- **When** validation runs
- **Then** exclusion integrity fails

### Requirement: Delete sanity
The validator SHALL quarantine a run that would tombstone more than the configured share of objects.
#### Scenario: delete spike
- **Given** a run that would tombstone 40 percent of a source's objects
- **When** validation runs
- **Then** the run is QUARANTINED with a delete-spike finding

### Requirement: Report
The validator SHALL produce a report with per-check results, counts and sample failures, visible in the UI.
#### Scenario: view report
- **Given** a finished run
- **When** the report is opened
- **Then** every check shows result and counts
