# Hackathon scope and boundaries

Goal of the demo: connect a source in the UI, pick what to pull, run the harvester, validate it, and watch the knowledge graph grow, then let an agent query it through MCP.

## In scope (must have)

### 1. UI (web app, container)
| Screen | What it does |
|---|---|
| Sources | List sources with status, last run, validation result; **Run** button per source (calls the dispatcher) |
| Add source wizard | Pick type, enter credentials, **Test connection**, **Discover** (tree of repos / databases / sites), tick scope, see the **harvest plan** (what will be pulled, size estimate, what is skipped), approve |
| Run view | Live status of a run: discovering, harvesting, validating, published or quarantined; counts and errors |
| Validation report | What was pulled versus expected, warnings, why a run was quarantined |
| **Knowledge graph** | Obsidian-style force-directed graph: nodes coloured by entity type, edges by relation; filter by source/type; search; click a node for the entity card (properties, edges, citations, harvested_at) |

Tech suggestion: React + Cytoscape.js (or react-force-graph) reading from the context service API.

### 2. Harvester framework
- Harvester pack per source system (see `docs/HARVESTERS.md`): connect, discover, profile, plan, harvest, validate.
- Source-aware scoping: never pull a whole 10 GB repo; pull only what the plan allows.
- Harvester validator that gates every run before knowledge is published.
- Source types for the demo:
  - **Git** with stack profiles: SQL, Java, .NET, Talend, shell scripts.
  - **SQL database** (use a Postgres container with sample data as the demo source): enter credentials, list databases, pick scope, pull metadata.
  - **Upload / documents** (docx, pdf, md, xlsx).

### 3. Dispatcher
Simple container service (no Airflow). The UI Run button and a basic cron call it. Behind a `Scheduler` boundary so Airflow can replace it later.

### 4. Store, ontology and MCP
Postgres + pgvector, ontology v0 with deterministic extraction first, `context-retrieval` MCP (`search_context`, `get_entity`, `get_related`, `get_lineage`).

## Stretch
- SharePoint harvester (Graph API; docs and Excel).
- Ontology proposal review screen.
- Live MCP fallback.
- Scheduled runs per source from the UI.

## Designed but not built (interface, docs and fixtures only)
Snowflake, Tableau, Salesforce, Talend Cloud API. Each gets a harvester pack folder with `harvester.yaml` and rules written, so the pattern is proven when it is time to build.

## Out of scope
Airflow, Cosmos DB, multi-tenant access control and SSO, per-user ACL propagation, editing the ontology in the UI, production hardening, cost reporting.

## Boundaries that protect the demo
- Every run has budgets (files, bytes, time, LLM tokens). The harvester stops and reports when one is hit.
- Metadata first. Data rows are never pulled by default; samples are opt-in and capped.
- Read-only credentials only. Credentials are never shown again after entry and never logged.
- A run that fails validation is quarantined; previous knowledge stays published.
- Local demo data only (sample repos, sample database, sample docs). No production credentials.
