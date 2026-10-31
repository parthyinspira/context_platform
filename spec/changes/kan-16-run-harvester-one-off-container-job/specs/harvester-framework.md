# Delta for harvester-framework

## ADDED Requirements
### Requirement: Harvester runs as a one-off container
The project SHALL provide a runner (`harvesters/run.py`, entrypoint `python -m harvesters.run`) that, given a `source_id` and a `plan_id` (the id of an already `PLANNED`/`APPROVED` `harvest_runs` row, whose `plan` column holds the `HarvestPlan`), drives `connect -> discover -> harvest -> normalize -> validate` for the registered `Harvester` of that source's type, records each state transition and the manifest on the `harvest_runs` row, evaluates the result with `PublishQuarantineGate`, and publishes `harvest.completed` on the `EventBus` with the run id, source id, final state, and `published`/`warning` flags. The runner SHALL read `SOURCE_ID`, `PLAN_ID` and `DATABASE_URL` from the environment (overridable by CLI flags), and SHALL NOT import any cloud-provider SDK, so the same container image runs unmodified under `docker compose run`, a GCP Cloud Run Job and an Azure Container Apps Job.

#### Scenario: runner-reads-source-id-and-plan-id-from-env-or-cli
- **Given** `SOURCE_ID` and `PLAN_ID` set as environment variables and no CLI flags given
- **When** the runner's argument parsing resolves its configuration
- **Then** it uses the environment values; explicit `--source-id`/`--plan-id` CLI flags, when given, take precedence over the environment

#### Scenario: runner-drives-full-lifecycle-to-published
- **Given** an `APPROVED` `harvest_runs` row with a stored plan and a source whose type has a registered `Harvester` that connects successfully and whose `validate()` returns `PASS`
- **When** the runner runs for that `source_id`/`plan_id`
- **Then** `harvest_runs.state` is written through `HARVESTING`, `VALIDATING` and finally `PUBLISHED`, the manifest reflects every discovered/fetched object, and `harvest.completed` is published with `published=true`

#### Scenario: runner-quarantines-on-failed-validation
- **Given** the same setup but the harvester's `validate()` returns `FAIL`
- **When** the runner runs
- **Then** `harvest_runs.state` ends at `QUARANTINED`, `harvest.completed` is published with `published=false`, and the recorded error names the validation failure

#### Scenario: runner-fails-cleanly-on-connect-error
- **Given** a harvester whose `connect()` returns `ok=False`
- **When** the runner runs
- **Then** `harvest_runs.state` is written as `FAILED` with the connect error recorded, and no `VALIDATING` or `PUBLISHED`/`QUARANTINED` transition is written

#### Scenario: runner-rejects-unknown-plan-id
- **Given** a `plan_id` with no matching `harvest_runs` row, or one that belongs to a different `source_id`
- **When** the runner runs
- **Then** it exits with a non-zero status, raises a clear error, and writes no `harvest_runs` row

#### Scenario: runner-is-platform-portable
- **Given** `harvesters/Dockerfile` and `harvesters/run.py`
- **When** they are inspected
- **Then** the image's `ENTRYPOINT`/`CMD` takes no positional platform-specific arguments, all configuration comes from environment variables, and no module under `harvesters/` imports a cloud-provider SDK outside `adapters/`
