## MODIFIED Requirements

### Requirement: Registration emits an event
The system SHALL publish `source.registered` through the `EventBus` when a source is created, and a consumer polling the same `EventBus` topic SHALL be able to receive that event.

#### Scenario: event on create
- **Given** a subscriber on `source.registered`
- **When** a source is created
- **Then** the subscriber receives the source id

#### Scenario: consumer-receives-source-registered
- **Given** a `POST /sources` request that will create a source, and an `EventBus` consumer polling the `source.registered` topic
- **When** the source is created and the consumer then polls `source.registered`
- **Then** the consumer receives exactly one event whose payload id matches the created source's id
