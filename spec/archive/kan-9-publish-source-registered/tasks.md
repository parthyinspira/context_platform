# Tasks

- [x] 1. Add consumer test `test_consumer_receives_source_registered_event` in `api/tests/test_source_registered_consumer.py`: wire `event_bus_dependency` to a real `PostgresOutboxEventBus` over a shared fake DB-API connection, `POST /sources`, then `poll("source.registered")` on that same bus instance and assert exactly one event with the created source's id (scenario: consumer-receives-source-registered) - test first
- [x] 2. Confirm the existing unit test covering scenario `event on create` still passes unchanged (no production code expected to change)
- [x] 3. Run `contract-check` and `secret-scan`
- [x] 4. `verification.md` completed with evidence per scenario
