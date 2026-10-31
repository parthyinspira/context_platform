# Tasks

- [x] 1. Add `harvesters/git/` package skeleton (`__init__.py`, `fixtures/`, `tests/__init__.py`) - test first: failing import test before the module exists
- [x] 2. Implement `extract_repository()` (scenario: repository-from-readme) - test first
- [x] 3. Implement `parse_codeowners()`, `classify_owner()`, `extract_owners()` (scenario: person-and-team-from-codeowners) - test first
- [x] 4. Implement `extract_manifest_module()` for `package.json` (scenario: module-and-dependency-from-package-json) - test first
- [x] 5. Extend `extract_manifest_module()` for `pom.xml` and `*.csproj` (scenarios: module-and-dependency-from-pom-xml, module-and-dependency-from-csproj) - test first
- [x] 6. Extend `extract_manifest_module()` for `requirements.txt` (repo-level dependencies, no synthetic module) (scenario: repo-level-dependency-from-requirements-txt) - test first
- [x] 7. Implement `normalize_repo()` combining the above with de-duplication by `external_id` (scenario: combined-normalize-repo) - test first
- [x] 8. Add determinism test: two calls with identical input produce identical output (scenario: no-llm-call)
- [x] 9. Add fixtures under `harvesters/git/fixtures/` (small README, package.json, pom.xml, csproj, requirements.txt, CODEOWNERS snippets) used by the tests above
- [x] 10. `ruff` passes on `harvesters/git/`; no new runtime dependency needed (stdlib `json`/`xml.etree.ElementTree` only), so `harvesters/requirements.txt` is unchanged
- [x] 11. Docs and contracts: new `spec/capabilities/git-normalize.md` only; no Ontology v0 / Postgres schema / Harvester interface change, no Confluence edit needed (run `contract-check`)
- [x] 12. `secret-scan` run over new fixtures and code (fixtures are synthetic, no real tokens)
- [x] 13. `verification.md` completed with evidence per scenario
