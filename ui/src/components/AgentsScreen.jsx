import { useState } from "react";
import { runAgentDemo } from "../api.js";
import { GraphCanvas } from "./GraphCanvas.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";

const AGENTS = [
  {
    id: "workflow",
    label: "Workflow",
    description: "Change-request impact analysis",
    tasks: [{ key: "rename-cust-id", label: "Rename column CUSTOMER.CUST_ID" }],
  },
  {
    id: "research",
    label: "Research",
    description: "How does customer data reach the revenue dashboard?",
    tasks: [{ key: "customer-to-revenue", label: "Customer data → Revenue Dashboard" }],
  },
  {
    id: "prod_support",
    label: "Prod Support",
    description: "Stale data triage",
    tasks: [{ key: "stale-revenue-dashboard", label: "Revenue dashboard shows stale data" }],
  },
  {
    id: "call_centre",
    label: "Call Centre",
    description: "Policy and product answers",
    tasks: [
      { key: "mid-year-contribution", label: "Mid-year contribution change rule" },
      { key: "out-of-scope", label: "Out-of-scope question (escalation demo)" },
    ],
  },
];

const DEMO_GRAPH = {
  nodes: [
    { id: "tbl-customer", label: "CUSTOMER", type: "Table" },
    { id: "col-cust-id", label: "CUST_ID", type: "Column" },
    { id: "job-etl-nightly", label: "etl_nightly_load", type: "Job" },
    { id: "tbl-revenue", label: "REVENUE_DAILY", type: "Table" },
    { id: "dash-revenue", label: "Revenue Dashboard", type: "Dashboard" },
    { id: "person-data-eng", label: "Alice Eng", type: "Person" },
    { id: "team-data", label: "Data Engineering", type: "Team" },
    { id: "svc-ingest", label: "CustomerIngestService", type: "Service" },
    { id: "doc-arch", label: "Data Architecture Overview", type: "Document" },
    { id: "job-broken-etl", label: "etl_weekly_transform", type: "Job" },
    { id: "person-oncall", label: "Bob Ops", type: "Person" },
    { id: "doc-runbook", label: "Revenue Pipeline Runbook", type: "Document" },
    { id: "doc-policy-contrib", label: "HSA Contribution Policy 2026", type: "Document" },
    { id: "doc-faq", label: "Member FAQ", type: "Document" },
  ],
  edges: [
    { id: "e1", source: "job-etl-nightly", target: "tbl-customer", relation: "READS_FROM" },
    { id: "e2", source: "job-etl-nightly", target: "tbl-revenue", relation: "WRITES_TO" },
    { id: "e3", source: "dash-revenue", target: "tbl-revenue", relation: "DERIVED_FROM" },
    { id: "e4", source: "col-cust-id", target: "tbl-customer", relation: "CONTAINS" },
    { id: "e5", source: "tbl-customer", target: "team-data", relation: "OWNED_BY" },
    { id: "e6", source: "tbl-customer", target: "person-data-eng", relation: "OWNED_BY" },
    { id: "e7", source: "svc-ingest", target: "tbl-customer", relation: "WRITES_TO" },
    { id: "e8", source: "job-broken-etl", target: "tbl-revenue", relation: "WRITES_TO" },
    { id: "e9", source: "job-broken-etl", target: "tbl-customer", relation: "READS_FROM" },
    { id: "e10", source: "tbl-revenue", target: "person-oncall", relation: "OWNED_BY" },
  ],
};

export function AgentsScreen() {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | running | done | error
  const [errorMsg, setErrorMsg] = useState("");
  const [showKb, setShowKb] = useState(true);

  async function handleRun() {
    if (!selectedAgent || !selectedTask) return;
    setStatus("running");
    setResult(null);
    setErrorMsg("");
    try {
      const data = await runAgentDemo(selectedAgent, selectedTask);
      setResult(data);
      setStatus("done");
    } catch (err) {
      setErrorMsg(err.message);
      setStatus("error");
    }
  }

  const agentTrace = showKb && result ? result.retrieved_node_ids : [];

  return (
    <div className="flex gap-6">
      {/* Left panel */}
      <div className="w-80 flex-shrink-0 space-y-4">
        <h2 className="text-lg font-semibold">Demo Agents</h2>

        {AGENTS.map((agent) => (
          <div
            key={agent.id}
            className={`cursor-pointer rounded-lg border p-3 ${
              selectedAgent === agent.id
                ? "border-accent bg-bg-surface"
                : "border-border-subtle bg-bg-surface opacity-80"
            }`}
            onClick={() => {
              setSelectedAgent(agent.id);
              setSelectedTask(agent.tasks[0].key);
              setResult(null);
              setStatus("idle");
            }}
            data-testid={`agent-card-${agent.id}`}
          >
            <div className="font-medium">{agent.label}</div>
            <div className="text-sm text-text-secondary">{agent.description}</div>
            {selectedAgent === agent.id && (
              <select
                className="mt-2 w-full rounded border border-border-subtle bg-bg-canvas px-2 py-1 text-sm"
                value={selectedTask}
                onChange={(e) => setSelectedTask(e.target.value)}
                data-testid="task-select"
              >
                {agent.tasks.map((t) => (
                  <option key={t.key} value={t.key}>
                    {t.label}
                  </option>
                ))}
              </select>
            )}
          </div>
        ))}

        <div className="flex items-center gap-2 pt-2">
          <input
            id="kb-toggle"
            type="checkbox"
            checked={showKb}
            onChange={(e) => setShowKb(e.target.checked)}
            data-testid="kb-toggle"
          />
          <label htmlFor="kb-toggle" className="text-sm">
            Show knowledge-base trace
          </label>
        </div>

        <button
          type="button"
          disabled={!selectedAgent || !selectedTask || status === "running"}
          onClick={handleRun}
          className="w-full rounded bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
          data-testid="run-btn"
        >
          {status === "running" ? "Running…" : "Run agent"}
        </button>
      </div>

      {/* Right panel */}
      <div className="min-w-0 flex-1 space-y-4">
        {status === "error" && <ErrorBanner message={errorMsg} />}

        {/* Graph with agent overlay */}
        <div>
          <div className="mb-1 flex items-center gap-2">
            <span className="text-sm font-medium">Knowledge graph</span>
            {agentTrace.length > 0 && (
              <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800" data-testid="trace-badge">
                {agentTrace.length} nodes retrieved
              </span>
            )}
          </div>
          <GraphCanvas nodes={DEMO_GRAPH.nodes} edges={DEMO_GRAPH.edges} agentTrace={agentTrace} />
        </div>

        {/* Step trace */}
        {result && (
          <div data-testid="agent-result">
            <h3 className="mb-2 font-medium">Agent steps</h3>
            <ol className="space-y-1 text-sm">
              {result.steps.map((step, i) => (
                <li key={i} className="flex gap-2">
                  <span className="w-6 flex-shrink-0 font-mono text-text-secondary">{i + 1}.</span>
                  <span>
                    <span className="mr-1 rounded bg-bg-surface px-1 text-xs uppercase text-text-secondary">
                      {step.kind}
                    </span>
                    {step.description}
                  </span>
                </li>
              ))}
            </ol>

            <h3 className="mb-2 mt-4 font-medium">Answer</h3>
            <pre
              className="whitespace-pre-wrap rounded bg-bg-surface p-3 text-sm"
              data-testid="agent-answer"
            >
              {result.answer}
            </pre>

            {result.escalated && (
              <div className="mt-2 rounded border border-warning bg-warning/10 px-3 py-2 text-sm text-warning" data-testid="escalation-flag">
                Escalated — no sufficient evidence found.
              </div>
            )}

            <h3 className="mb-2 mt-4 font-medium">Citations</h3>
            <ul className="space-y-1 text-sm" data-testid="citations-list">
              {result.citations.map((c, i) => (
                <li key={i} className="flex gap-2">
                  <a
                    href={c.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-accent underline"
                  >
                    {c.entity_name}
                  </a>
                  <span className="text-text-secondary">
                    · {c.harvested_at.slice(0, 10)} · {c.sensitivity}
                  </span>
                </li>
              ))}
              {result.citations.length === 0 && (
                <li className="text-text-secondary">No citations (escalated).</li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
