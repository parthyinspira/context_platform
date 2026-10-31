# Delta for harvest-validation

## MODIFIED Requirements
### Requirement: Standard checks
The validator SHALL check completeness, exclusion integrity, budget compliance, parse success, expected yield, ontology conformance, referential integrity, delete sanity, secrets/PII and freshness. (was: requirement named all ten checks with only one scenario, for exclusion integrity; this change adds scenarios for completeness, budget compliance, parse success, ontology conformance, referential integrity and freshness — the seven checks in scope for KAN-83. Expected yield, delete sanity and secrets/PII remain unimplemented, covered by later stories.)

#### Scenario: excluded type fetched
- **Given** a manifest containing a file type the plan excluded
- **When** validation runs
- **Then** exclusion integrity fails

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
