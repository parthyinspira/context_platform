# Tasks

- [x] 1. Write `api/tests/test_sources.py` covering validation failures (type, uri, schedule, credentials_ref, owner, sensitivity) and the success path (scenarios: reject invalid type/uri/schedule/credentials_ref/owner/sensitivity, register a source) - test first
- [x] 2. Add `api/app/schemas.py` with the `SourceCreate` request model and cron-syntax validation
- [x] 3. Add `api/app/db.py` for a psycopg connection factory from `DATABASE_URL`
- [x] 4. Add `POST /sources` route in `api/app/main.py`: validate, insert with `status='active'`, publish `source.registered` via `adapters.factory.get_event_bus`, return id + row (scenario: register a source)
- [x] 5. Add `psycopg[binary]` to `api/requirements.txt`; wire `adapters` package into the `api` Docker build context
- [x] 6. Run tests (`api/tests`) and confirm all pass
- [x] 7. Docs and contracts reviewed (spec/capabilities/source-registry.md delta applied at archive; CLAUDE.md schema unchanged; Confluence not affected — no schema/ontology change)
- [x] 8. verification.md completed
