# KAN-14: Normalize repo: README, manifests, CODEOWNERS

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-14   Epic: 3 Git harvester end to end (KAN-11)   Branch: kepler/kan-14-normalize-repo-readme-manifests

## Why
The Git harvester's `normalize()` step (`docs/HARVESTERS.md` section 4, "Entities from Git: Repository, Module, Job, Table ..., Person/Team (from CODEOWNERS)") needs deterministic extraction for the parts of a repository that are not SQL (already spiked in KAN-25) and not yet covered by any other story: the README, dependency manifests (`package.json`, `pom.xml`, `*.csproj`, `requirements.txt`), and `CODEOWNERS`. Per CLAUDE.md ("Deterministic extraction first") and `docs/HARVESTERS.md` rule 9, this must not call an LLM.

No `harvesters/git/` package exists yet (confirmed: `harvesters/` only has `base.py`, `framework/`, `registry.py` — the Git harvester itself is not built). Following the precedent set by KAN-25 (SQL lineage spike built as a standalone, harvester-independent module ahead of the harvester that will call it), this story adds a standalone deterministic extraction module inside the `harvesters` package that a future `GitHarvester.normalize()` can call once discover/harvest exist, using the real `harvesters.base.Entity`/`Edge` types (which did not exist yet when KAN-25 was built).

## What changes
- Add `harvesters/git/normalize.py`:
  - `extract_repository(repo_name, source_id, readme_text=None) -> Entity` — one `Repository` entity; if a README is given, its first `# Title` / first non-blank line becomes `props["description"]`.
  - `parse_codeowners(text) -> list[CodeownersRule]` — one rule per non-comment, non-blank line: `(pattern, owners)`.
  - `classify_owner(owner: str) -> Literal["Person", "Team"]` — GitHub CODEOWNERS convention: `@org/team-name` (contains `/`) is a `Team`; `@username` or a bare email is a `Person`.
  - `extract_owners(repo_entity, codeowners_text, source_id) -> (list[Entity], list[Edge])` — one `Person`/`Team` entity per distinct owner across all rules, plus one `OWNED_BY` edge per `(repo, owner)` pair (`src=Repository`, `dst=Person`/`Team`).
  - `extract_manifest_module(path, text, repo_entity, source_id) -> (Entity | None, list[Entity], list[Edge])` — parses one manifest (`package.json`, `pom.xml`, `*.csproj`, `requirements.txt`) with the standard library (`json`, `xml.etree.ElementTree`, line parsing) into: a `Module` entity named per the manifest's own declared name (`package.json` `name`, `pom.xml` `artifactId`, `*.csproj` filename stem); a `Module` entity per declared dependency (name only, no version); and a `DEPENDS_ON` edge from the manifest's module to each dependency module. `requirements.txt` has no declared module name of its own, so its dependencies attach directly to the `Repository` entity instead of a synthetic module.
  - `normalize_repo(source_id, repo_name, readme_text, manifests, codeowners_text) -> (list[Entity], list[Edge])` — the single entry point a future `GitHarvester.normalize()` calls; combines the above, de-duplicating entities by `external_id`.
- External ids: `repo:<repo_name>`, `module:<repo_name>:<module_name>` (manifest's own module) or `module:<dep_name>` (a dependency, repo-independent since the same dependency can be shared), `person:<handle>`, `team:<org>/<team>`.
- Unit tests with small fixtures covering each manifest type, CODEOWNERS owner/team classification, and the combined `normalize_repo()`.
- Extend `fixtures/repos/sql-dbt-sample/` is out of scope; instead this story's own fixtures live under `harvesters/git/fixtures/` (manifest/README/CODEOWNERS snippets), since the existing `fixtures/repos/*` trees and `fixtures/EXPECTED.md` (KAN-88) are owned by the fixtures capability and don't yet include README/manifest/CODEOWNERS content — adding that is tracked separately, not bundled into this story.

## In scope
- Deterministic parsing of: `README.md`/`README` (title/description only), `package.json`, `pom.xml`, `*.csproj`, `requirements.txt`, `CODEOWNERS`.
- `Repository`, `Module`, `Person`, `Team` entities; `OWNED_BY`, `DEPENDS_ON` edges — the exact AC: "creates Repository, Module, Person/Team entities and OWNED_BY/DEPENDS_ON edges deterministically."
- Unit tests and small fixtures under `harvesters/git/fixtures/`.

## Out of scope
- Wiring into a real `GitHarvester` (no `connect`/`discover`/`harvest` for Git exists yet; tracked by other Epic 3 stories).
- Per-path CODEOWNERS-to-Module resolution (e.g. matching a CODEOWNERS glob to the specific Module it covers). This story attaches every `OWNED_BY` edge to the `Repository` entity; refining ownership to module granularity is future work once a harvester supplies real file paths.
- Persisting to Postgres (no normalizer/writer wiring for Git entities exists yet).
- `Job`/`Table` entities and `READS_FROM`/`WRITES_TO` edges from Git (SQL lineage already covered by KAN-25; Talend/job lineage tracked separately).
- Transitive dependency resolution, version constraints, or lockfiles — only directly declared dependencies in the manifest itself.
- Updating `fixtures/repos/*` or `fixtures/EXPECTED.md` (separate fixtures capability, KAN-88).

## Acceptance criteria (from Jira)
1. Creates Repository, Module, Person/Team entities and OWNED_BY/DEPENDS_ON edges deterministically -> scenarios: repository-from-readme, module-and-dependency-from-package-json, module-and-dependency-from-pom-xml, module-and-dependency-from-csproj, repo-level-dependency-from-requirements-txt, person-and-team-from-codeowners, combined-normalize-repo, no-llm-call (purely deterministic: same input twice gives identical output).

## Affected
Capabilities: `spec/capabilities/git-normalize.md` (new). Docs/contracts: no change to Ontology v0 types/relations (all four entity types and both edge relations already exist in CLAUDE.md's Ontology v0 list) or the Postgres schema — this story only produces `harvesters.base.Entity`/`Edge` values shaped to the existing contract. No Confluence Contracts update needed.

## Risks and open questions
- CODEOWNERS ownership is attached at the repository level, not per-module/path, until a real harvester supplies file paths to match against CODEOWNERS glob patterns — documented as a known gap above.
- `pom.xml`/`.csproj` are parsed with `xml.etree.ElementTree` (stdlib); malformed XML is reported by raising rather than silently skipped, consistent with "report, don't drop" (`docs/HARVESTERS.md` rule 11), but there is no manifest/outcome-recording wiring yet since there is no harvest run to record into.

## Approval
Approved by: auto (user started spec-auto), 2026-10-31; human review at PR
