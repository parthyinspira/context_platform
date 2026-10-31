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
The validator SHALL check completeness, exclusion integrity, budget compliance, parse success, expected yield, ontology conformance, referential integrity, delete sanity, secrets/PII and freshness. `harvest_validation/validator.py` has two aggregator entry points: `run_checks` for the three checks that need no manifest (exclusion integrity, expected yield, secrets/PII), composing the legacy `harvesters.base.ValidationReport`; and `validate` for the six manifest-driven checks (completeness, budget compliance, parse success, ontology conformance, referential integrity, freshness) plus exclusion integrity, composing the richer `harvest_validation.report.ValidationReport`. Unifying them into one call is left to whichever story wires the validator into a concrete harvester.
#### Scenario: excluded type fetched
- **Given** a manifest containing a file type the plan excluded
- **When** validation runs
- **Then** exclusion integrity fails

#### Scenario: zero yield fails
- **Given** a run whose detected stacks produced zero entities of any type
- **When** the expected-yield check runs
- **Then** the check fails with a zero-yield detail

#### Scenario: stack missing expected entities fails
- **Given** a run that detected a stack (for example SQL/dbt) but emitted no entities of that stack's expected type (Table)
- **When** the expected-yield check runs
- **Then** the check fails naming the stack with no matching entities

#### Scenario: expected yield passes
- **Given** a run whose detected stacks each produced at least one entity of an expected type
- **When** the expected-yield check runs
- **Then** the check passes

#### Scenario: unredacted secret fails
- **Given** stored text for a fetched object that still contains an unredacted secret pattern
- **When** the secrets/PII check runs
- **Then** the check fails naming the offending object

#### Scenario: redacted content passes
- **Given** stored text for every fetched object with no unredacted secret pattern remaining
- **When** the secrets/PII check runs
- **Then** the check passes

#### Scenario: completeness ratio below fail threshold fails
- **Given** a manifest where the fetched share of discovered objects is below the completeness fail threshold
- **When** validation runs
- **Then** completeness fails and the report names the ratio

#### Scenario: completeness ratio in warn band warns
- **Given** a manifest where the fetched share of discovered objects is at or above the fail threshold but below the warn threshold
- **When** validation runs
- **Then** completeness warns

#### Scenario: completeness full coverage passes
- **Given** a manifest where every discovered object was fetched, skipped or failed with a reason and the fetched share meets the warn threshold
- **When** validation runs
- **Then** completeness passes

#### Scenario: budget exceeded warns and notes partial
- **Given** a run whose recorded usage exceeds a budget on the plan
- **When** validation runs
- **Then** budget compliance warns, names the exceeded budget, and the message notes the run as PARTIAL

#### Scenario: budget within limits passes
- **Given** a run whose recorded usage is within every budget on the plan
- **When** validation runs
- **Then** budget compliance passes

#### Scenario: parse success below fail threshold fails
- **Given** a file type whose share of fetched objects parsed without error is below the parse-success fail threshold
- **When** validation runs
- **Then** parse success fails and names the type

#### Scenario: parse success in warn band warns per type
- **Given** a file type whose parse-success share is at or above the fail threshold but below the warn threshold, while other types are fully parsed
- **When** validation runs
- **Then** parse success warns and names only the affected type

#### Scenario: unknown entity type fails ontology conformance
- **Given** an emitted entity whose type is not in the ontology v0 entity types
- **When** validation runs
- **Then** ontology conformance fails and names the entity

#### Scenario: missing required field fails ontology conformance
- **Given** an emitted entity missing `source_id`, `external_id`, `harvested_at` or `ontology_version`
- **When** validation runs
- **Then** ontology conformance fails and names the missing field

#### Scenario: edge with unknown relation fails ontology conformance
- **Given** an emitted edge whose relation is not in the ontology v0 relation types, or missing `source_id`, `harvested_at` or `ontology_version`
- **When** validation runs
- **Then** ontology conformance fails and names the edge

#### Scenario: dangling edge warns referential integrity
- **Given** an emitted edge whose source or destination external id matches no emitted entity
- **When** validation runs
- **Then** referential integrity warns and names the edge

#### Scenario: resolved edge passes referential integrity
- **Given** every emitted edge's source and destination external ids match an emitted entity
- **When** validation runs
- **Then** referential integrity passes

#### Scenario: cursor not advanced warns freshness
- **Given** a completed run whose cursor did not advance
- **When** validation runs
- **Then** freshness warns

#### Scenario: report aggregates worst status across checks
- **Given** a run where one check fails, one warns and the rest pass
- **When** validation runs
- **Then** the overall `ValidationReport.status` is FAIL, and the report lists a result, counts and sample failures for every check

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
