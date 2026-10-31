# Delta for harvest validation

## MODIFIED Requirements
### Requirement: Standard checks
The validator SHALL check completeness, exclusion integrity, budget compliance, parse success, expected yield, ontology conformance, referential integrity, delete sanity, secrets/PII and freshness. (was: same wording; this delta adds scenarios for expected yield and secrets/PII — delete sanity already had a scenario and is unchanged)

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
