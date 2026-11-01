# Context Platform – Demo Script

Walks through the four demo steps from `CLAUDE.md` end to end using the fixture sources bundled in `fixtures/`.

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Docker Desktop | 4+ | WSL2 backend on Windows |
| jq | any | `apt install jq` / `brew install jq` |
| curl | any | bundled on macOS/Linux/WSL2 |

The full compose stack must be healthy before running the demo:

```bash
docker compose up -d
# Wait ~60 s for all services to be healthy
docker compose ps          # migrate should be exited(0); rest healthy
curl http://localhost:8000/health   # {"status":"ok"}
curl http://localhost:8002/health   # {"status":"ok"} (MCP context-retrieval)
```

## Running the demo

```bash
bash demo/demo.sh
```

The script runs unattended and prints human-readable output for each step.

## What each step does

### Step 1 – Register source
`POST /sources` registers the `sql-dbt-sample` fixture repo (a local git path, no external network call).
Expected output: JSON with a new source `id`, `status: "registered"`.

### Step 2 – Watch harvest complete
`POST /sources/{id}/runs` kicks off the harvester.
The script polls `/sources/{id}/runs/{run_id}` every 5 s until `state` reaches `PUBLISHED` (≤ 2.5 min).
Expected entity counts from `fixtures/EXPECTED.md`:
- Entities: Repository, Module(stg_orders), Module(mart_orders), Table(source_orders)
- Edges: DERIVED_FROM(mart_orders→stg_orders), DERIVED_FROM(stg_orders→source_orders)

### Step 3 – Query the knowledge base
Calls the `context-retrieval` MCP (`/search_context`) asking which tables `mart_orders` depends on.
Only the sql-dbt-sample source is in scope — the answer must come from it, with citations.
Expected: at least one result citing `stg_orders` or `source_orders`, with `source_url` and `harvested_at`.

### Step 4 – Upload a document and query
Registers `fixtures/docs/orders-faq.md` as an upload source, waits for it to be published, then searches for order processing rules.
Expected: passage from the FAQ with citation (`source_url`, `harvested_at`, `sensitivity=internal`).

## Fixture sources (non-sensitive)

All sources under `fixtures/` contain synthetic data only:

| Path | Type | What it models |
|------|------|----------------|
| `fixtures/repos/sql-dbt-sample` | Git/dbt | Order staging + mart models |
| `fixtures/repos/java-sample` | Git/Java | Orders service repository |
| `fixtures/repos/dotnet-sample` | Git/.NET | Orders service (.NET) |
| `fixtures/repos/talend-sample` | Git/Talend | ETL load job (contains a clearly-labeled fake secret for redaction tests) |
| `fixtures/db/init.sql` | SQL | Postgres seed schema + stale-job simulation |
| `fixtures/docs/orders-faq.md` | Document | Synthetic FAQ (sensitivity=internal) |
| `fixtures/docs/data-retention-policy.md` | Document | Synthetic policy (sensitivity=restricted) |
| `fixtures/docs/sample_report.xlsx` | Document | Synthetic report |

No production credentials, no real API keys, no PII.

## Troubleshooting

- **Timeout on PUBLISHED**: the harvester or normalizer may not be running. Check `docker compose logs harvester`.
- **MCP returns no results**: the embeddings service may still be loading the model. Wait 60 s and retry.
- **Port conflicts**: adjust `*_PORT` variables in `.env` and update `API`/`MCP` at the top of `demo.sh`.
