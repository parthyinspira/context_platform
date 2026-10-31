# Delta for dispatcher (new capability)

## ADDED Requirements

### Requirement: POST /sources/{id}/run starts a harvest run
The system SHALL accept `POST /sources/{id}/run` for an existing, `active` source, record a run in `dispatcher_runs` with status `queued`, publish `harvest.requested` on the `EventBus` with the run id, source id, source type and uri, and return the run id and status. The system SHALL NOT use Airflow for this.

#### Scenario: run an active source
- **Given** an existing source with status `active`
- **When** `POST /sources/{id}/run` is called
- **Then** the response is `201` with the new run's id, source id and status `queued`, and `harvest.requested` is published with that run id

#### Scenario: run an unknown source
- **Given** no source exists with the given id
- **When** `POST /sources/{id}/run` is called
- **Then** the response is `404` and no run is recorded

#### Scenario: run an inactive source
- **Given** an existing source with a status other than `active`
- **When** `POST /sources/{id}/run` is called
- **Then** the response is `409` and no run is recorded

### Requirement: GET /sources/due lists sources due for a run
The system SHALL expose `GET /sources/due` returning every `active` source whose next scheduled run (from its cron `schedule` and `last_harvest_at`) is not after the current time; a source never harvested SHALL always be due.

#### Scenario: never-harvested source is due
- **Given** an active source with `last_harvest_at` null
- **When** `GET /sources/due` is called
- **Then** that source is included in the response

#### Scenario: recently harvested source is not due
- **Given** an active source whose cron schedule's next run (from `last_harvest_at`) is in the future
- **When** `GET /sources/due` is called
- **Then** that source is not included in the response

#### Scenario: source past its schedule is due
- **Given** an active source whose cron schedule's next run (from `last_harvest_at`) is not after now
- **When** `GET /sources/due` is called
- **Then** that source is included in the response

#### Scenario: inactive sources are excluded
- **Given** a source with a status other than `active`
- **When** `GET /sources/due` is called
- **Then** that source is not included in the response, regardless of schedule
