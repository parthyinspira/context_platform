# Tasks

- [x] 1. Add `pyproject.toml` with a shared `ruff` config (target `api/`, `scheduler/`, `adapters/`) (scenario: ci-lint-runs)
- [x] 2. Add `ruff==0.7.4` to `api/requirements-dev.txt`, `scheduler/requirements-dev.txt`, `adapters/requirements-dev.txt`; run `ruff check` locally and fix any violations it finds
- [x] 3. Add `.github/workflows/ci.yml` with a `lint` job (ruff over the three Python packages) and `test` jobs (pytest per Python package, `node --test` for `ui/test`) (scenarios: ci-lint-runs, ci-test-runs)
- [x] 4. Add a `compose-smoke-test` job to the workflow running on `ubuntu-latest`: `docker compose up -d`, wait/poll for healthy, curl each `/health` endpoint, `docker compose logs` on failure, `docker compose down -v` (scenario: ci-compose-smoke-linux)
- [x] 5. Re-read `CLAUDE.md` against the current repo (`docker-compose.yml`, `adapters/`, migrations) and fix any drift found (scenario: claude-md-documents-contracts)
- [x] 6. Run `contract-check` and `secret-scan` skills
- [x] 7. `verification.md` completed with evidence per scenario
