# Delta for harvest-validation

## MODIFIED Requirements
### Requirement: Validation gates publishing
The system SHALL run the validator after harvest and SHALL publish knowledge only when status is PASS or WARN. The decision SHALL be made by a `PublishQuarantineGate` that only acts on a run in the `VALIDATING` state. (was: publish-vs-quarantine decision described but not implemented)

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
