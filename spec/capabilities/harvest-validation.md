# Capability: harvest validation

### Requirement: Validation gates publishing
The system SHALL run the validator after harvest and SHALL publish knowledge only when status is PASS or WARN.
#### Scenario: failed validation
- **Given** a run whose validator status is FAIL
- **When** the gate evaluates
- **Then** the run is QUARANTINED and previously published knowledge is unchanged

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
