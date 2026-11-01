# Demo script: all four agents with graph trace overlay

Audience: hackathon judges and stakeholders.
Duration: ~15 minutes total (3–4 minutes per agent).
Prerequisites: `docker compose up` stack running; UI at http://localhost:5173.

---

## Setup (before the room fills)

1. `docker compose up --wait` — all services healthy.
2. Open the UI in a browser at **http://localhost:5173**.
3. Navigate to **Knowledge Graph** — confirm nodes are visible (14 demo nodes seeded).
4. Navigate to **Agents** — confirm four agent cards are listed.

---

## Agent A — Workflow: change-request impact (3 min)

**Scenario:** The team wants to rename column `CUSTOMER.CUST_ID` to `CUSTOMER.CUSTOMER_ID`.

**Cue sheet:**

| # | Speaker action | What the audience sees |
|---|---|---|
| 1 | Click **Workflow** agent card | Card expands; task "Rename column CUSTOMER.CUST_ID" is pre-selected |
| 2 | Confirm **Show knowledge-base trace** is checked | Toggle checked |
| 3 | Click **Run agent** | "Running…" spinner; step trace streams in left panel |
| 4 | Point to step 1: `search_context(['CUST_ID', 'CUSTOMER'])` | Step trace shows 1 Column found |
| 5 | Point to step 3: `get_lineage(downstream, depth=3)` | Downstream assets listed: REVENUE_DAILY, Revenue Dashboard |
| 6 | Point to the graph | CUSTOMER, REVENUE_DAILY, Revenue Dashboard, Alice Eng, Data Engineering — **amber pulsing borders**, numbered 1–5 in retrieval order |
| 7 | Read the Answer: affected assets, required approvers, suggested tests | Audience sees a complete, cited change plan |
| 8 | Click a citation → node highlights on graph | Graph focuses on the cited node |

**Pass condition:** REVENUE_DAILY and Revenue Dashboard listed as affected; Alice Eng / Data Engineering listed as owners; no invented assets.

---

## Agent B — Research: how does customer data reach the dashboard? (3 min)

**Scenario:** A new team member asks "How does customer data reach the revenue dashboard?"

| # | Speaker action | What the audience sees |
|---|---|---|
| 1 | Click **Research** agent card | Pre-selected task: "Customer data → Revenue Dashboard" |
| 2 | Click **Run agent** | Steps stream; 2 search steps + 1 lineage expansion |
| 3 | Point to step trace: `search_context(docs, ...)` | Architecture Overview chunk retrieved |
| 4 | Point to the Answer | 3-step chain: CustomerIngestService → CUSTOMER → REVENUE_DAILY → Dashboard; each step cited |
| 5 | Point to: "UNVERIFIED — no evidence found" | Deliberately false Kafka claim is flagged and removed |
| 6 | Point to graph overlay | 9 nodes lit up in retrieval order |

**Pass condition:** Chain correctly described; false claim flagged as UNVERIFIED.

---

## Agent C — Prod support: stale data triage (4 min)

**Scenario:** PagerDuty alert: "Revenue dashboard shows stale data."

| # | Speaker action | What the audience sees |
|---|---|---|
| 1 | Click **Prod Support** agent card | Pre-selected task: "Revenue dashboard shows stale data" |
| 2 | Click **Run agent** | 5 steps: identify dashboard, upstream lineage, freshness check, owners, runbook search |
| 3 | Point to step 2: `get_lineage(upstream, depth=3)` | etl_weekly_transform found as upstream feeder |
| 4 | Point to step 3: `get_source_status(dash-revenue)` | Last harvested timestamp shown |
| 5 | Point to the Answer | Cause #1: `etl_weekly_transform` (seeded as broken); owner: Bob Ops; runbook link |
| 6 | Point to graph overlay | job-broken-etl node is highlighted #3; Revenue Dashboard is #1 |

**Pass condition:** `etl_weekly_transform` appears as top probable cause; runbook cited.

---

## Agent D — Call centre: policy answers (3 min)

**Scenario A (in-scope):** A call-centre rep asks "What is the rule for a mid-year contribution change?"

| # | Speaker action | What the audience sees |
|---|---|---|
| 1 | Click **Call Centre** agent card | Task: "Mid-year contribution change rule" |
| 2 | Click **Run agent** | Step: search policy + FAQ docs |
| 3 | Point to the Answer | Quoted passage from HSA Contribution Policy 2026; source URL; effective date 2026-01-01 |
| 4 | Confirm no restricted docs in citations | Only internal-sensitivity docs cited |

**Scenario B (out-of-scope escalation):**

| # | Speaker action | What the audience sees |
|---|---|---|
| 5 | Change task to **"Out-of-scope question (escalation demo)"** | Dropdown updates |
| 6 | Click **Run agent** | Single search step; 0 results |
| 7 | Point to **Escalated** banner | "I cannot find this information… Escalating to a specialist." — no citations |

**Pass condition:** Correct answer with citation for in-scope; escalation banner for out-of-scope; no restricted content.

---

## Graph trace overlay — summary talking points

> "Every amber-bordered node is a knowledge-base call the agent made. The number on the node is the retrieval order — you can see exactly what evidence the agent used, and in what sequence, without looking at logs."

- Toggle **Show knowledge-base trace** off → overlay clears instantly.
- Toggle back on → overlay re-applies.
- This is the same knowledge graph the harvest pipeline populates; what you see during the agent run is a live view of the data the agent is grounding on.

---

## Fallback (if backend is unavailable)

The agents module can be run directly in Python for a command-line demo:

```bash
cd <repo-root>
python - <<'EOF'
from agents.workflow.agent import run
import json, dataclasses
r = run("rename-cust-id")
print("Answer:", r.answer[:300])
print("Nodes retrieved:", r.retrieved_node_ids)
EOF
```

Expected output includes `tbl-revenue`, `dash-revenue`, `person-data-eng` in the node list.
