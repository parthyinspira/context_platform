# Verification

Status: PASS
Date: 2026-10-30   Commit: working tree on top of b6939c9 (pre-PR)

## Checks
| Check | Result |
|---|---|
| Lint (`ruff check api scheduler adapters --config pyproject.toml`) | All checks passed (10 pre-existing violations fixed to make the new lint gate clean) |
| Tests (`api`) | `python -m pytest` from `api/` -> 1/1 passed |
| Tests (`scheduler`) | `python -m pytest` from `scheduler/` -> 1/1 passed |
| Tests (`adapters`) | `python -m pytest adapters/tests -q` -> 9/9 passed |
| Tests (`ui`) | `node --test test/*.test.js` from `ui/` -> 1/1 passed |
| compose-smoke-test logic | `docker compose up -d` locally (Linux containers via Docker Desktop) -> all 5 services `healthy`; `curl /health` on ports 8000, 8001, and UI port (remapped to 3100 locally to avoid a host conflict) all returned `{"status":"ok"}`; `docker compose down -v` cleaned up |
| contract-check | `grep -rn "google.cloud\|boto3\|azure\." --include="*.py" . \| grep -v /adapters/` -> no matches; no schema/ontology/harvester-interface files touched |
| secret-scan | Diff scanned for key/token/password/PEM patterns -> only a `secrets.get("LLM_API_KEY")` lookup by name, no literal secret value; `git ls-files` has no tracked `.env` |
| Definition of Done | All tasks ticked |

## Scenario evidence
| Requirement / Scenario | Evidence | Result |
|---|---|---|
| Lint CI / ci-lint-runs | `.github/workflows/ci.yml` `lint` job runs `ruff check api scheduler adapters --config pyproject.toml`; same command run locally -> "All checks passed!" | PASS |
| Test CI / ci-test-runs | `.github/workflows/ci.yml` `test-python` job (matrix over `api`, `scheduler`, `adapters`) and `test-ui` job; each command run locally with the results above | PASS |
| Compose smoke test / ci-compose-smoke-linux | `.github/workflows/ci.yml` `compose-smoke-test` job (`ubuntu-latest`): `docker compose up -d`, poll for healthy, curl 3 `/health` endpoints, `docker compose down -v`; the same sequence run locally on Linux containers (see table above) succeeded end to end | PASS (workflow shape validated locally; not yet run on an actual GitHub Actions runner — see Not verified) |
| CLAUDE.md documents contracts / claude-md-documents-contracts | Re-read `CLAUDE.md`: "## Architecture" section matches current `docker-compose.yml`/`adapters/` layout; "### Ontology v0" lists the 10 entity types and 7 relations matching `spec/capabilities/*.md`; "### Harvester interface" gives the exact `discover`/`fetch`/`normalize` class shape used by `docs/HARVESTERS.md`. No drift found; no edit needed | PASS |

## Acceptance criteria
| Criterion | Scenarios | Result |
|---|---|---|
| Repo has lint CI | ci-lint-runs | PASS |
| Repo has test CI | ci-test-runs | PASS |
| CLAUDE.md documents architecture, ontology v0, harvester interface | claude-md-documents-contracts | PASS |

## Not verified
- **Actual GitHub Actions execution**: `.github/workflows/ci.yml` has not run on a real Actions runner yet (no push to the remote from this session before PR). Its `lint`, `test-python`, `test-ui` steps are the exact commands verified locally above; the `compose-smoke-test` job's `docker compose up`/health-check/`down` sequence was verified locally against the same `docker-compose.yml` on Linux containers, but GitHub's `ubuntu-latest` runner environment (image pulls, resource limits, networking) is unverified until the PR triggers CI. Will be visible as a status check on the PR.
- **Windows CI runner**: not added (out of scope per proposal.md; Windows was already verified locally in KAN-101).
