# Architecture: topology and hierarchy

End goal: expose the platform as MCP servers so agents and LLMs can discover, query and (with limits) manage enterprise context. This page shows the layers, the data hierarchy and the MCP surface. Contracts (schema, ontology, harvester interface) live in `CLAUDE.md` and the Confluence Contracts page.

## 1. System topology

```mermaid
flowchart TD
    subgraph Sources
        G[Git repos]
        D[Doc sites]
        U[Uploads GCS]
        X[Future: Snowflake / Tableau / Confluence]
    end

    subgraph UI["UI — React, port 3000"]
        GRAPH[Knowledge Graph]
        PIPE[Pipelines]
        CHAT[Chat]
        AGTS[Agents]
        MCPUI[Settings - MCP]
    end

    subgraph API["Control plane — FastAPI, port 8000"]
        REG[(sources table)]
        SRVC[Source registry API]
        NORM_API[POST /normalize/run_id]
        ONT_API[POST /ontology/extract]
        CHAT_API[POST /agents/chat]
        DSP[Dispatcher]
    end

    subgraph Harvest["Harvesters — one-off containers"]
        HG[Git harvester]
        HD[Doc harvester]
        HU[Upload harvester]
    end

    subgraph Process["Normalization and ontology"]
        RAW[(Raw payloads)]
        NORM[Tier 1 Normalizer - per source]
        ONT[Tier 2 Ontology extractor - cross source]
    end

    subgraph Store["Knowledge store — Postgres + pgvector"]
        ENT[(entities)]
        EDG[(edges)]
        CHK[(chunks)]
        RUNS[(harvest_runs)]
    end

    subgraph Serve["Serving — port 8003"]
        MCP_SRV[MCP server - streamable HTTP]
        EXT_MCP[External MCP servers]
    end

    ANTHROPIC[Anthropic API]

    G & D & U & X --> Harvest
    SRVC --> REG
    REG --> DSP --> Harvest
    Harvest --> RAW --> NORM
    NORM_API --> NORM
    NORM --> ENT & EDG & CHK & RUNS
    ONT_API --> ONT
    ONT --> ENT & EDG
    ENT & EDG & CHK --> MCP_SRV
    CHAT_API --> ANTHROPIC
    CHAT_API --> MCP_SRV
    CHAT_API --> EXT_MCP
    UI --> SRVC
    UI --> NORM_API & ONT_API & CHAT_API
    MCPUI -.->|stored in localStorage| EXT_MCP
```

### Layers and responsibilities

| Layer | Component | Runtime (local / GCP / Azure) | Responsibility |
|---|---|---|---|
| 0 Sources | Git, docs, uploads | n/a | Systems of record; never modified |
| 1 UI | React app (Vite) | Nginx container / Cloud Run / Container Apps | Knowledge graph, pipelines, chat, agent editor, MCP settings |
| 2 Control plane | Registry API (FastAPI), dispatcher, scheduler | compose scheduler + Postgres outbox / Cloud Run, Scheduler, Pub/Sub / Container Apps, Service Bus | CRUD sources, trigger harvests, expose run history |
| 3 Harvest | One harvester per source type | one-off containers / Cloud Run Jobs / Container Apps Jobs | discover, fetch, emit raw objects incrementally |
| 4 Normalize (Tier 1) | Per-source normalizer — `POST /normalize/{run_id}` | same API container | Raw → entities, edges, chunks, embeddings per source |
| 5 Ontology (Tier 2) | Cross-source extractor — `POST /ontology/extract` | same API container | SQL lineage (sqlglot), Python imports, name matching → cross-source edges |
| 6 Store | entities, edges, chunks, proposed_changes, harvest_runs | Cloud SQL + pgvector | Single source of truth for knowledge |
| 7 Serve | MCP server (`/mcp`, streamable-HTTP) | container / Cloud Run / Container Apps | search_context, get_entity, get_graph, get_lineage, list_sources |
| 8 Chat | `POST /agents/chat` → Anthropic agentic loop | same API container | Up to 6 tool-call rounds; proxies external MCP servers |

### UI screens (hackathon)

| Screen | Nav key | Purpose |
|---|---|---|
| Knowledge Graph | Graph | Full-viewport force-directed graph; source filter, entity legend, Build Ontology toggle |
| Pipelines | Pipelines | Per-source pipeline cards: Harvest → Normalize → Build Ontology; per-source scheduler toggle |
| Sources | Sources | Register, list, delete sources; launch harvest runs |
| Agents | Agents | Agent library (demo + custom); editor with system prompt, model, tool assignment |
| Chat | Chat | Unified dropdown: select agent / Knowledge Graph / Direct Model; Anthropic API backend |
| MCP Tools | MCP | Built-in tool docs; external MCP server management (stored in localStorage) |
| Settings | Settings | Models, Chunking, Extraction, Project config |

## 2. Data hierarchy

### 2.1 Entity containment (what lives inside what)

```
Source (registry row)
└── Repository / Document site / Upload set
    ├── Module / Service
    │   ├── Job (ETL, pipeline)
    │   │   ├── READS_FROM  -> Table
    │   │   └── WRITES_TO   -> Table
    │   └── Document (README, design doc)
    │       └── Chunk (embedding + citation)
    ├── Table
    │   └── Column
    │       └── DERIVED_FROM -> Column  (lineage)
    ├── Dashboard
    │   └── READS_FROM -> Table
    └── Person / Team
        └── OWNED_BY (from Repository, Module, Table, Dashboard)
```

### 2.2 Ontology layers

| Layer | Contents | Changes |
|---|---|---|
| Core ontology (versioned file) | Entity and relation types | Rarely, via reviewed PR; bumps `ontology_version` |
| Facts | entities and edges with `source_id`, `confidence`, `ontology_version` | Every harvest |
| Proposals | `proposed_changes`: new types, low-confidence facts, entity merges | Queue, auto-apply only above threshold for known types |
| Chunks | Text spans with embeddings, linked to an entity | Every harvest; re-embedded when `embedding_model` changes |

### 2.3 Retrieval hierarchy (how a query is answered)

```
Agent question
└── Context service
    ├── 1. Filter: sensitivity / source / type / not tombstoned
    ├── 2. Candidate search: keyword + vector (chunks)
    ├── 3. Graph expansion: edges from matched entities (depth-limited)
    ├── 4. Rerank + token budget
    └── 5. Response: results + citations (source link, harvested_at, sensitivity)
```

## 3. MCP topology

Each MCP server is a thin, stateless container service over the context service. Transport: streamable HTTP. All tool results include citations and freshness.

```
Agent / LLM (MCP client)
├── context-retrieval  (read-only, default for all agents)
│   ├── tools
│   │   ├── search_context(query, filters?, limit?)
│   │   ├── get_entity(id | external_id)
│   │   ├── get_related(entity, relation?, depth?, direction?)
│   │   ├── get_lineage(entity, direction=upstream|downstream, depth?)
│   │   ├── list_sources(type?, status?)
│   │   └── get_source_status(source_id)        # last_harvest_at, errors, freshness
│   ├── resources
│   │   ├── ontology://v{n}                      # entity and relation types
│   │   └── entity://{id}                        # entity card with edges
│   └── prompts
│       └── explain_asset, impact_analysis, find_owner
│
├── context-admin  (write, restricted, audit-logged)
│   ├── register_source(type, uri, schedule, credentials_ref, owner, sensitivity)
│   ├── update_source(id, schedule?, status?)
│   ├── trigger_harvest(source_id)
│   └── review_proposal(id, approve|reject)
│
└── live MCPs  (fallback when indexed context is stale or missing)
    ├── git       (read file, blame, log)
    └── snowflake (describe table, sample rows; read-only role)
```

### MCP design rules
- **Retrieval first, live second.** The context service answers from the index. Agents call live MCPs only when `get_source_status` shows stale data or the item is not indexed; label results as `indexed` or `live`.
- **Small, well-described tool surface.** Each tool does one thing; descriptions say when to use it.
- **Always return provenance:** `source_url`, `harvested_at`, `sensitivity`, `confidence` where relevant.
- **Token budgets:** results are truncated or paginated; include `next_cursor`.
- **Separate servers by risk.** Read tools and write tools are different servers so permissions can differ per agent.
- **Identity and permissions:** each call carries a caller identity; the context service filters by `sensitivity` and source access. Every call is audit-logged (caller, query, returned source IDs).
- **No secrets through MCP.** `credentials_ref` is never returned; live MCPs use their own service accounts.

### Example agent flow
```
User: "What breaks if we change table CUSTOMER?"
 1. search_context("CUSTOMER table")            -> entity Table:CUSTOMER
 2. get_lineage(Table:CUSTOMER, downstream, 3)  -> Jobs, Tables, Dashboards
 3. get_related(each Dashboard, OWNED_BY)       -> owners
 4. get_source_status(source of CUSTOMER)       -> fresh within SLA? else live MCP check
 5. Answer with cited assets, owners and freshness
```

## 4. Build mapping (Jira epics)

| Epic | Delivers |
|---|---|
| 1 Foundation | compose stack, Postgres + pgvector, adapters, schema, CI |
| 2 Source registry and API | Control plane, `source.registered` |
| 3 Git harvester | First harvester, entities and chunks |
| 4 Scheduler and incremental | Dispatcher, idempotent upserts, tombstones |
| 5 Ontology updater | Deterministic and LLM extraction, proposals |
| 6 Retrieval MCP and context service | `context-retrieval` server |
| 7 Upload harvester | GCS-driven ingestion |
| 8 Demo, evals, docs | Golden questions, demo, docs |

Suggested additions (not yet in Jira): a `context-admin` MCP story under Epic 2 or 6, and MCP auth/audit under Epic 6.

## 4b. Portability (containers first, Azure-ready)

| Concern | Interface | Local default | GCP | Azure |
|---|---|---|---|---|
| Events | `EventBus` | Postgres outbox | Pub/Sub | Service Bus |
| Files / raw | `ObjectStore` | folder or MinIO | GCS | Blob Storage |
| Secrets | `SecretStore` | env / Docker secrets | Secret Manager | Key Vault |
| LLM / embeddings | `LLMProvider` | Anthropic API or Ollama | Vertex AI | Azure AI Foundry |
| Scheduling | dispatcher | compose scheduler | Cloud Scheduler + Cloud Run Jobs | Container Apps Jobs (cron) |
| Database | plain SQL + pgvector | Postgres container | Cloud SQL | Azure Database for PostgreSQL Flexible Server |

Rule: business logic imports only the interfaces; cloud SDKs live in `adapters/`. Hackathon: run locally, deploy once to GCP (free trial). Later: deploy the same images to Azure by switching adapter config.

## 5. Evolution path
1. Hackathon: Postgres + pgvector for relationships; one retrieval MCP; Git and upload harvesters.
2. Next: Snowflake/Confluence/Tableau harvesters, live MCP fallback, review queue UI.
3. Scale: dedicated graph store only if traversal depth or latency requires it; AlloyDB for vectors at volume; per-user ACL propagation from source systems.


