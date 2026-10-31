# Tasks

- [x] 1. `HarvestRunStore`: load a `harvest_runs` row by `plan_id` + `source_id` (error on missing/mismatch), load `sources` row, write state/manifest/error updates - test first against a fake Postgres connection (scenario: runner-rejects-unknown-plan-id)
- [x] 2. `harvesters/run.py` config resolution: `SOURCE_ID`/`PLAN_ID`/`DATABASE_URL` from env, CLI flags override (scenario: runner-reads-source-id-and-plan-id-from-env-or-cli)
- [x] 3. Runner happy path: connect -> discover -> harvest -> normalize -> manifest -> validate -> gate -> PUBLISHED, `harvest.completed` published (scenario: runner-drives-full-lifecycle-to-published)
- [x] 4. Runner quarantine path: validator FAIL -> QUARANTINED, `harvest.completed` with `published=false` (scenario: runner-quarantines-on-failed-validation)
- [x] 5. Runner connect-failure path: FAILED, no further transitions (scenario: runner-fails-cleanly-on-connect-error)
- [x] 6. `harvesters/Dockerfile` + `docker-compose.yml` `harvester` service (scenario: runner-is-platform-portable)
- [x] 7. `docs/HARVESTERS.md` "Running a harvest" section
- [x] 8. Wire `harvesters` package (already in ruff include/CI matrix) requirements for psycopg; confirmed no cloud SDK imports (contract-check)
- [x] 9. verification.md completed
