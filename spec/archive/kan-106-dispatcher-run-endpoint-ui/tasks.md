# Tasks

- [x] Migration `0003_dispatcher_runs` (up/down)
- [x] `scheduler/app/db.py` connection factory (mirrors `api/app/db.py`)
- [x] `scheduler/app/schemas.py` (`RunOut`, `DueSourceOut`)
- [x] `scheduler/app/due.py` (`is_due` cron logic)
- [x] `POST /sources/{id}/run` in `scheduler/app/main.py`
- [x] `GET /sources/due` in `scheduler/app/main.py`
- [x] `scheduler/conftest.py` import-path shim (mirrors `api/conftest.py`)
- [x] Tests: `scheduler/tests/test_dispatcher.py` (run happy path, 404, 409, due-sources cases)
- [x] `scheduler/requirements.txt`: add `psycopg[binary]`, `croniter`
- [x] `scheduler/Dockerfile` + `docker-compose.yml`: build scheduler from repo root context so it can `COPY adapters`
- [x] Spec delta `specs/dispatcher.md` (new capability)
- [x] `verification.md` with evidence per scenario and AC
- [x] Run `contract-check` and `secret-scan`
- [x] Run `scripts/spec_check.py` (plan and verify stages)
