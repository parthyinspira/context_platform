# Context Platform

Container-first project (hackathon on local Docker + a GCP free-trial deploy; later reused on Azure): harvest registered sources (Git repos, documents, uploads) on a schedule, normalize them into Postgres (+ pgvector), keep an ontology/graph up to date, and serve context to agents via MCP.

Tracking: Jira project `KAN` (epics 1-8). Docs: Confluence space `SD`, page "Context Platform (Hackathon) - Project Home" and its child "Contracts". The Confluence Contracts page is the source of truth for the schema, ontology and harvester interface; update it in the same PR when you change any of them.

## Architecture
- Everything runs as containers (`docker compose` locally). Cloud services are reached only through small adapter interfaces so the same images run on local Docker, GCP and Azure.
- Source registry (`sources` table) drives onboarding and scheduling. A new source is a row, never a code change.
- Harvesters are one-off containers, one per source type, launched by a dispatcher on a schedule (compose scheduler locally; Cloud Run Jobs / Container Apps Jobs in cloud).
- Events `source.registered`, `harvest.completed`, `ontology.updated` go through an `EventBus` interface. Default implementation: Postgres outbox (no extra infra); adapters for Pub/Sub and Azure Service Bus.
- Uploads and raw payloads use an `ObjectStore` interface: local folder/MinIO by default; adapters for GCS and Azure Blob. Raw metadata may also live in Postgres `jsonb`.
- Knowledge, edges and vectors: Postgres + pgvector in a container (Cloud SQL / Azure Database for PostgreSQL Flexible Server in cloud). No cloud-specific SQL.
- LLMs through an `LLMProvider` interface: Meta Llama (hackathon credits, OpenAI-compatible endpoint configured in `.env`) by default; adapters for Anthropic, Vertex AI and Azure AI Foundry. Embeddings through a separate `EmbeddingProvider`: a local open model (Ollama or sentence-transformers) in its own container by default.
- Secrets through a `SecretStore` interface: env/Docker secrets locally; Secret Manager / Key Vault in cloud. One identity per component.
- Context service and MCP servers are stateless containers (Cloud Run / Container Apps in cloud).

Flow: source registered -> harvester (discover/fetch/normalize) -> `harvest.completed` -> normalizer writes entities, edges, chunks, embeddings -> ontology updater (propose, validate, apply) -> `ontology.updated`.

## Scope and design docs
- `docs/HACKATHON_SCOPE.md`: what is in and out for the hackathon (UI with knowledge graph, harvesters, validator, dispatcher).
- `docs/HARVESTERS.md`: harvester lifecycle, scoping rules per source, validator, skills and rules. Read before touching any harvester.
- `spec/`: capability specs, active changes, workflow stage specs and templates.
- `docs/ARCHITECTURE.md`: topology, data hierarchy, MCP design, portability.
- Harvesters must follow the budgets and metadata-first rules in `docs/HARVESTERS.md`; a run that fails validation is quarantined, never published.

## Docs index (read only the section you need)
- Architecture, adapters, MCP surface: `docs/ARCHITECTURE.md` (only for service or adapter work).
- Harvesters, scoping, validator rules: `docs/HARVESTERS.md` (only for harvester or validator work).
- UI screens, tokens, graph behaviour: `docs/UI_DESIGN.md` (only for UI work).
- Demo agents and grounding pattern: `docs/DEMO_AGENTS.md` (only for agent work).
- Scope and bundles: `docs/HACKATHON_SCOPE.md`, `docs/MILESTONES.md` (only to check scope or order).
- Process: `spec/README.md`; lite mode is the default, see `spec/workflow/07-lite.md`.
Take acceptance criteria from the task description when present; call Jira only if they are missing.

## Contracts

### Harvester interface
```python
class Harvester:
    def connect(self, source) -> ConnectionResult
    def discover(self, source) -> ScopeTree
    def profile(self, source, scope) -> Profile
    def plan(self, profile) -> HarvestPlan
    def harvest(self, source, plan, cursor) -> Iterable[RawObject]
    def normalize(self, raw) -> list[Entity | Edge | Chunk]
    def validate(self, plan, manifest) -> ValidationReport
```
- Incremental via `sources.last_cursor`; upserts are idempotent, keyed by stable `external_id`.
- Objects not seen in a harvest get `tombstoned_at`; retrieval excludes tombstoned rows.
- Every record carries `source_id` and `harvested_at`.
- Each run is tracked in `harvest_runs`, progressing CONNECTING -> DISCOVERING -> PROFILING -> PLANNED -> APPROVED -> HARVESTING -> VALIDATING -> PUBLISHED, or to QUARANTINED, FAILED or PARTIAL.

### Ontology v0
- Entities: Repository, Service, Module, Table, Column, Dashboard, Job, Document, Person, Team.
- Relations: DEPENDS_ON, READS_FROM, WRITES_TO, DERIVED_FROM, DOCUMENTS, OWNED_BY, CONTAINS.
- Deterministic extraction first (manifests, SQL lineage via sqlglot, CODEOWNERS). LLM extraction only for unstructured text, constrained to this ontology, with a citation and confidence per assertion.
- New types or low-confidence facts go to `proposed_changes`; known types with high confidence auto-apply.
- Every fact stores `ontology_version`, `source_id`, `confidence`.

### Postgres schema v0
- `sources(id, type, uri, schedule, credentials_ref, owner, sensitivity, status, last_harvest_at, last_cursor, config_json)`
- `entities(id, type, name, source_id, external_id, props jsonb, ontology_version, tombstoned_at)`
- `edges(id, src_entity_id, dst_entity_id, relation, confidence, source_id, ontology_version)`
- `chunks(id, entity_id, source_id, text, embedding vector, embedding_model, metadata jsonb, harvested_at)`
- `harvest_runs(id, source_id, state, plan jsonb, manifest jsonb, error, started_at, updated_at)`
- `proposed_changes(id, kind, payload jsonb, confidence, status, created_at)`

## Conventions
- Python 3.12, type hints, small modules. One harvester class per source type in `harvesters/`, registered by `source.type`.
- Schema changes go through migrations only. Never edit tables by hand.
- Record `embedding_model` on every chunk; chunk by structure (function, section, table), not fixed windows.
- Never store or log secret values; `credentials_ref` is a key resolved by `SecretStore`.
- No direct imports of cloud SDKs outside `adapters/`; business logic depends on the interfaces only.
- Every service has a Dockerfile and runs from `docker compose up`.
- Tests for every harvester (fixture repos/docs) and for idempotent re-harvest.
- Retrieval results always include source link, `harvested_at` and `sensitivity`.

## Entry rules for any agent or tool (Kepler, Claude Code, others)
These apply whatever the launching prompt says.
- Asked to work on, plan or implement a Jira story (`KAN-n`): start with the `spec-plan` skill. Do not write or edit code, migrations or config until the user has approved the plan.
  - Exception: when the user explicitly starts `spec-auto` (one story) or `spec-batch` (a milestone), that request counts as the plan approval; follow those skills, record it in `proposal.md`, and still obey their stop conditions.
- Never merge a PR, push to `main`, or bypass a stage gate. Never skip `spec-verify` before opening a PR.
- If a skill or doc conflicts with the launching prompt, follow the skill and doc and tell the user.
- If the Jira story cannot be read, ask the user to paste it; never invent acceptance criteria.
- Stay inside the approved proposal; anything else becomes a new Jira story.

## Workflow (spec-driven; see `spec/README.md` and `spec/workflow/`)
Default is lite mode (`spec/workflow/07-lite.md`): one `plan.md` and one short `verification.md` per story; Docker checks, contract check, one reviewer run and archive once per bundle.
Development tooling: stories are picked up from Jira (via Kepler or the Atlassian MCP) and built with Claude Code in VS Code.
1. One Jira story (`KAN-n`) = one change folder `spec/changes/kan-<n>-<slug>/` and one branch/PR.
2. Plan (`spec-plan`): proposal, spec deltas, tasks; the user approves before any code.
3. Develop (`spec-develop`): test-first, stay inside the proposal's scope.
4. Verify (`spec-verify`): `verification.md` with evidence per scenario; Status PASS before a PR.
5. PR (`spec-pr`): title starts with the story key; template filled; CI green.
6. Review (`spec-review`): `story-reviewer` agent in a fresh context; the user merges only on `APPROVE`.
7. After merge (`spec-archive`): deltas applied to `spec/capabilities/`, change archived, Jira story Done.
Specs in `spec/capabilities/` are the source of truth for behaviour; update Confluence if a contract changed.

## Build order
Epic 1 Foundation (compose stack, Postgres+pgvector, adapters, CI) -> 2 Source registry/API -> 3 Git harvester -> 4 Scheduler/incremental -> 5 Ontology updater -> 6 Retrieval MCP -> 7 Upload harvester -> 8 Demo, evals, docs. Get a thin end-to-end demo working by the halfway point, even if rough.


## Demo script
1. `POST /sources` with a new Git repo.
2. Watch harvest, normalization and ontology update complete.
3. Ask the agent a question only that repo can answer; check citations.
4. Upload a document and ask about it.
