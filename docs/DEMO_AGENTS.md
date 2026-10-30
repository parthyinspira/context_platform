# Demo agents: using the knowledge base as the grounding step

Four demo agents show how any agent can use the platform. Each one does its own work first, and its **last step** calls the `context-retrieval` MCP to ground, verify or enrich the result before acting. (The same tools can also be used earlier in a flow.)

## 1. Shared pattern: the grounding step

```
Agent works on task
  -> final step: Grounding
       1. search_context / get_entity     find the relevant assets or documents
       2. get_related / get_lineage       expand to dependencies, owners, downstream impact
       3. get_source_status               check freshness; if stale, use a live MCP
       4. Compose answer with citations   every claim has source link + harvested_at
       5. Refuse or escalate              no evidence -> say so, do not guess
```

Contract every demo agent follows:
- Output separates **claims** from **evidence**; each claim carries a citation (`source_url`, `harvested_at`, `sensitivity`).
- Claims with no evidence are flagged "unverified" or dropped.
- Stale evidence (older than the source's freshness target) is labelled, with the live-check result if available.
- The agent's role limits what it can see: results are filtered by `sensitivity` for the caller identity.

## 2. The four agents

### A. Workflow agent: change-request impact
- **Task:** a change ticket arrives ("rename column CUSTOMER.CUST_ID"); the agent drafts the change plan and routes approvals.
- **Grounding step:** `search_context` for the table and column, `get_lineage(downstream, depth 3)` for jobs, tables and dashboards that break, `get_related(OWNED_BY)` for owners.
- **Output:** impact report (affected assets with citations), required approvers, suggested test list, draft ticket comment.
- **Demo data:** a sample SQL repo and a Talend-style repo with a lineage chain to a dashboard.
- **Pass if:** all known downstream assets and owners are listed, none invented.

### B. Research agent: "how does X work here?"
- **Task:** answer an open question, such as "how does customer data reach the revenue dashboard?"
- **Flow:** plan sub-questions, gather from documents and code, synthesize.
- **Grounding step:** every claim in the draft is checked with `search_context`; unsupported claims are removed or marked; related assets found through `get_related` are added as "also see".
- **Output:** short report with a claim-to-citation table and a confidence note.
- **Pass if:** each claim is cited and a deliberately false claim planted in the draft is flagged.

### C. Production support agent: stale data triage
- **Task:** an alert says "Revenue dashboard shows stale data"; the agent triages.
- **Flow:** read the alert, identify the asset, check recent job status.
- **Grounding step:** `get_lineage(upstream)` to list the feeding jobs and tables, `get_related(OWNED_BY)` for who to page, runbook documents via `search_context`, `get_source_status` to see whether the index itself is fresh; live MCP check of the suspect source if stale.
- **Output:** probable causes ranked by evidence, owner to contact, runbook steps, links.
- **Pass if:** the real broken upstream job (seeded in the demo data) is in the top two causes.

### D. Call-centre agent: policy and product answers
- **Task:** a customer service rep (or voice or chat bot) asks, "what is the rule for a mid-year contribution change?"
- **Grounding step:** `search_context` over uploaded policy, FAQ and product documents with `sensitivity <= internal`; answer only from retrieved passages, quote the source and effective date.
- **Rules:** never answer without a source ("I can't find this, escalating"); never expose restricted documents; log every retrieval.
- **Output:** short answer, the quoted passage, source link, escalation flag.
- **Pass if:** correct answer with citation for in-scope questions, escalation for out-of-scope ones, no restricted content returned.

## 3. How they are built
- One small agent loop per demo in `agents/<name>/`, using an MCP client and the `LLMProvider` interface (Llama via your credits by default). Tool calling and structured output support must be confirmed for the chosen model.
- A shared `grounding.py` implements the pattern above, so each agent differs only in its task prompt and role.
- Deterministic mock tasks and seeded demo data make the demo repeatable.

## 4. Demo UI: agent runs with a retrieval trace
Add an **Agents** screen: pick an agent, give it a task, and watch (1) its steps, (2) each knowledge-base call, and (3) **the nodes it retrieved lighting up in the knowledge graph**. The final answer shows citations that link to the node cards.

## 5. Evaluation
- Each agent has 5 to 10 golden tasks with expected evidence (source IDs that must appear).
- Metrics: citation coverage, hallucinated claim count (target 0), correct escalation rate, retrieval hit rate.
- Run in CI with the demo data; fail below thresholds.
