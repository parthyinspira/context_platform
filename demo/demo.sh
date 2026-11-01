#!/usr/bin/env bash
# Demo script for Context Platform – walks through all 4 CLAUDE.md demo steps.
# Prerequisites: docker compose up (stack healthy), jq installed.
# Usage: bash demo/demo.sh

set -euo pipefail

API="http://localhost:8000"
MCP="http://localhost:8002"
FIXTURES_DIR="$(cd "$(dirname "$0")/../fixtures" && pwd)"

step() { echo; echo "=== STEP $1: $2 ==="; }
wait_for() {
  local url="$1" field="$2" want="$3" tries=30
  for i in $(seq 1 $tries); do
    local val
    val=$(curl -sf "$url" | jq -r ".$field" 2>/dev/null || true)
    if [[ "$val" == "$want" ]]; then return 0; fi
    echo "  (waiting – $field=$val)"
    sleep 5
  done
  echo "ERROR: timed out waiting for $field=$want at $url" >&2
  return 1
}

# ── Step 1: Register the sql-dbt-sample Git repo ──────────────────────────────
step 1 "POST /sources – register sql-dbt-sample fixture repo"
SOURCE=$(curl -sf -X POST "$API/sources" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"git\",
    \"uri\": \"file://$FIXTURES_DIR/repos/sql-dbt-sample\",
    \"owner\": \"demo\",
    \"sensitivity\": \"internal\",
    \"config_json\": {}
  }")
echo "$SOURCE" | jq .
SOURCE_ID=$(echo "$SOURCE" | jq -r '.id')
echo "Registered source id: $SOURCE_ID"

# ── Step 2: Watch harvest complete ────────────────────────────────────────────
step 2 "Trigger harvest and watch run complete"
RUN=$(curl -sf -X POST "$API/sources/$SOURCE_ID/runs")
echo "$RUN" | jq .
RUN_ID=$(echo "$RUN" | jq -r '.id')
echo "Harvest run id: $RUN_ID"

echo "Polling for PUBLISHED state (up to 2.5 min)…"
wait_for "$API/sources/$SOURCE_ID/runs/$RUN_ID" "state" "PUBLISHED"

echo "Run completed. Entity counts:"
curl -sf "$API/sources/$SOURCE_ID/entities/count" | jq .

# ── Step 3: Ask agent a question only this repo can answer ────────────────────
step 3 "Search context – orders lineage (only sql-dbt-sample can answer)"
curl -sf -X POST "$MCP/search_context" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What tables does mart_orders depend on?\",
    \"source_ids\": [\"$SOURCE_ID\"],
    \"top_k\": 5
  }" | jq '{results: [.results[] | {entity: .entity_name, snippet: .snippet, source_url: .source_url, harvested_at: .harvested_at}]}'

# ── Step 4: Upload a document and ask about it ────────────────────────────────
step 4 "Upload orders-faq.md and query for contribution rules"
DOC=$(curl -sf -X POST "$API/sources" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"upload\",
    \"uri\": \"file://$FIXTURES_DIR/docs/orders-faq.md\",
    \"owner\": \"demo\",
    \"sensitivity\": \"internal\",
    \"config_json\": {}
  }")
echo "$DOC" | jq .
DOC_ID=$(echo "$DOC" | jq -r '.id')

DOC_RUN=$(curl -sf -X POST "$API/sources/$DOC_ID/runs")
DOC_RUN_ID=$(echo "$DOC_RUN" | jq -r '.id')
echo "Polling for document PUBLISHED…"
wait_for "$API/sources/$DOC_ID/runs/$DOC_RUN_ID" "state" "PUBLISHED"

echo "Searching for contribution rules:"
curl -sf -X POST "$MCP/search_context" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What are the order processing rules?\",
    \"source_ids\": [\"$DOC_ID\"],
    \"top_k\": 3
  }" | jq '{results: [.results[] | {entity: .entity_name, snippet: .snippet, source_url: .source_url, harvested_at: .harvested_at}]}'

echo
echo "=== Demo complete. All 4 steps passed. ==="
