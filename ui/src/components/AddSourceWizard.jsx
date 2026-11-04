import { useEffect, useState } from "react";
import { ScopeTree } from "./ScopeTree.jsx";
import { PlanSummaryCard } from "./PlanSummaryCard.jsx";
import { Skeleton } from "./Skeleton.jsx";
import { createRun, createSource, discoverSource, planSource, testConnection } from "../api.js";

const DEFAULT_SCHEDULE = "0 0 * * *";
const DEFAULT_OWNER = "unassigned";
const DEFAULT_SENSITIVITY = "internal";

const SOURCE_TYPES = [
  {
    id: "git",
    label: "Git Repository",
    icon: "⎇",
    description: "GitHub, GitLab, Bitbucket or any Git remote",
    enabled: true,
  },
  {
    id: "sql",
    label: "SQL Database",
    icon: "🗄",
    description: "PostgreSQL, MySQL, SQL Server",
    enabled: false,
  },
  {
    id: "snowflake",
    label: "Snowflake",
    icon: "❄",
    description: "Snowflake data warehouse tables & views",
    enabled: false,
  },
  {
    id: "upload",
    label: "File Upload",
    icon: "📄",
    description: "PDF, Word, Excel, CSV documents",
    enabled: false,
  },
  {
    id: "sharepoint",
    label: "SharePoint",
    icon: "🔗",
    description: "SharePoint Online document libraries",
    enabled: false,
  },
  {
    id: "tableau",
    label: "Tableau",
    icon: "📊",
    description: "Tableau workbooks & dashboards",
    enabled: false,
  },
];

// Curated list of popular repos users can pick instead of typing
const POPULAR_REPOS = [
  { label: "Claim Processor UI",          url: "https://github.com/parthyinspira/claim-processor-ui" },
  { label: "Claim Processor API",         url: "https://github.com/parthyinspira/claim-processor-api" },
  { label: "Claim Processor Data Integration", url: "https://github.com/parthyinspira/claim-processor-data-integration" },
  { label: "Claim Processor Snowflake",   url: "https://github.com/parthyinspira/claim-processor-snowflake" },
  { label: "Claim Processor Power BI",    url: "https://github.com/parthyinspira/claim-processor-powerbi" },
  { label: "OpenEMR",                     url: "https://github.com/openemr/openemr" },
  { label: "HAPI FHIR",                   url: "https://github.com/hapifhir/hapi-fhir" },
  { label: "Medplum",                     url: "https://github.com/medplum/medplum" },
  { label: "TigerShark (EDI X12)",        url: "https://github.com/Arborian/TigerShark" },
  { label: "CAS ChainLadder (Actuarial)", url: "https://github.com/casact/chainladder-python" },
  { label: "Apache Fineract (Core Banking)", url: "https://github.com/apache/fineract" },
  { label: "Medusa (eCommerce)",          url: "https://github.com/medusajs/medusa" },
];

const STEPS = ["Type", "Connect", "Discover", "Plan & Run"];

// ── helpers ──────────────────────────────────────────────────────────────────

function scopeNodeFromApi(node) {
  return {
    id: node.id,
    label: node.name,
    count: node.size_hint ?? undefined,
    checked: false,
    children: (node.children ?? []).map(scopeNodeFromApi),
  };
}

function setAllChecked(nodes, checked) {
  return nodes.map((n) => ({ ...n, checked, children: setAllChecked(n.children ?? [], checked) }));
}

function toggleTree(nodes, targetId) {
  return nodes.map((n) => {
    if (n.id === targetId) {
      const next = !n.checked;
      return { ...n, checked: next, children: setAllChecked(n.children ?? [], next) };
    }
    if (n.children?.length) {
      const children = toggleTree(n.children, targetId);
      return { ...n, checked: children.every((c) => c.checked), children };
    }
    return n;
  });
}

function matchesQuery(node, query) {
  if (node.label.toLowerCase().includes(query)) return true;
  return (node.children ?? []).some((c) => matchesQuery(c, query));
}

function filterTree(nodes, query) {
  if (!query) return nodes;
  return nodes
    .filter((n) => matchesQuery(n, query))
    .map((n) => ({ ...n, children: filterTree(n.children ?? [], query) }));
}

function selectAllLeaves(nodes) {
  return nodes.map((n) => {
    if (!n.children?.length) return { ...n, checked: true };
    const children = selectAllLeaves(n.children);
    return { ...n, children, checked: children.every((c) => c.checked) };
  });
}

function collectCheckedLeafIds(nodes) {
  return nodes.flatMap((n) =>
    n.children?.length ? collectCheckedLeafIds(n.children) : n.checked ? [n.id] : []
  );
}

function parsePatternList(text) {
  return text.split(",").map((p) => p.trim()).filter(Boolean);
}

// ── sub-components ────────────────────────────────────────────────────────────

function StepIndicator({ steps, active }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: 32 }}>
      {steps.map((s, i) => {
        const done = i < active;
        const current = i === active;
        return (
          <div key={s} style={{ display: "flex", alignItems: "center", flex: i < steps.length - 1 ? 1 : "none" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
              <div style={{
                width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                background: done ? "#059669" : current ? "#2563EB" : "var(--border-subtle)",
                color: done || current ? "#fff" : "var(--text-secondary)",
                fontWeight: 700, fontSize: 14,
              }}>
                {done ? "✓" : i + 1}
              </div>
              <span style={{ fontSize: 12, fontWeight: current ? 600 : 400, color: current ? "#2563EB" : done ? "#059669" : "var(--text-secondary)", whiteSpace: "nowrap" }}>
                {s}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div style={{ flex: 1, height: 2, background: done ? "#059669" : "var(--border-subtle)", margin: "0 8px", marginBottom: 20 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function Card({ children, style }) {
  return (
    <div style={{
      background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 12,
      padding: "24px 28px", boxShadow: "0 1px 3px rgba(0,0,0,.06)",
      ...style,
    }}>
      {children}
    </div>
  );
}

function InfoBox({ children }) {
  return (
    <div style={{ background: "#1e3a5f", border: "1px solid #2563EB44", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#93C5FD", lineHeight: 1.5 }}>
      {children}
    </div>
  );
}

function ErrorBox({ message }) {
  if (!message) return null;
  return (
    <div style={{ background: "#3b0f0f", border: "1px solid #DC262644", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#FCA5A5" }}>
      {message}
    </div>
  );
}

function SuccessBox({ message }) {
  return (
    <div style={{ background: "#052e16", border: "1px solid #05966944", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#6EE7B7" }}>
      ✓ {message}
    </div>
  );
}

function PrimaryBtn({ children, onClick, disabled, style }) {
  return (
    <button type="button" onClick={onClick} disabled={disabled} style={{
      background: disabled ? "#93C5FD" : "#2563EB", color: "#fff",
      border: "none", borderRadius: 8, padding: "9px 20px",
      fontWeight: 600, fontSize: 14, cursor: disabled ? "not-allowed" : "pointer",
      ...style,
    }}>
      {children}
    </button>
  );
}

function GhostBtn({ children, onClick }) {
  return (
    <button type="button" onClick={onClick} style={{
      background: "transparent", color: "var(--text-secondary)",
      border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "9px 20px",
      fontWeight: 500, fontSize: 14, cursor: "pointer",
    }}>
      {children}
    </button>
  );
}

// ── main component ────────────────────────────────────────────────────────────

export function AddSourceWizard({ onSourceCreated, onRunStarted, onCancel }) {
  const [step, setStep] = useState(0);
  const [type, setType] = useState(null);
  const [uri, setUri] = useState("");
  const [credentialsInput, setCredentialsInput] = useState("");
  const [pendingCredentials, setPendingCredentials] = useState("");
  const [testState, setTestState] = useState("idle");
  const [testError, setTestError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [createdSource, setCreatedSource] = useState(null);
  const [scopeState, setScopeState] = useState("idle");
  const [scopeNodes, setScopeNodes] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [planState, setPlanState] = useState("idle");
  const [planData, setPlanData] = useState(null);
  const [includeText, setIncludeText] = useState("");
  const [excludeText, setExcludeText] = useState("");
  const [runSubmitting, setRunSubmitting] = useState(false);
  const [runError, setRunError] = useState(null);
  const [showRepoList, setShowRepoList] = useState(false);
  const [repoFilter, setRepoFilter] = useState("");

  function selectType(sourceType) { setType(sourceType); setStep(1); }

  function handleCredentialsChange(value) { setCredentialsInput(value); setTestState("idle"); }

  async function handleTestConnection() {
    setTestState("loading"); setTestError(null);
    try {
      const result = await testConnection({ type, uri, credentials_ref: credentialsInput });
      if (result.ok) {
        setPendingCredentials(credentialsInput);
        setCredentialsInput("");
        setTestState("success");
      } else {
        setTestState("error");
        setTestError(result.error ?? "Connection failed");
      }
    } catch {
      setTestState("error");
      setTestError("Could not reach the API server");
    }
  }

  async function handleAddSource() {
    setSubmitting(true); setSubmitError(null);
    try {
      const source = await createSource({
        type, uri,
        credentials_ref: pendingCredentials || "public",
        schedule: DEFAULT_SCHEDULE,
        owner: DEFAULT_OWNER,
        sensitivity: DEFAULT_SENSITIVITY,
      });
      setPendingCredentials("");
      setCreatedSource(source);
      setStep(2);
      onSourceCreated?.(source);
    } catch {
      setSubmitError("Could not create the source — check the API is reachable");
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    if (step !== 2 || !createdSource) return;
    let cancelled = false;
    setScopeState("loading");
    discoverSource(createdSource.id)
      .then((tree) => {
        if (cancelled) return;
        setScopeNodes((tree.roots ?? []).map(scopeNodeFromApi));
        setScopeState("success");
      })
      .catch(() => { if (!cancelled) setScopeState("error"); });
    return () => { cancelled = true; };
  }, [step, createdSource]);

  const visibleScopeNodes = filterTree(scopeNodes, searchQuery.trim().toLowerCase());
  const scopeTreeRenderState =
    scopeState === "success" && scopeNodes.length === 0 ? "empty" : scopeState;

  function handleGoToPlan() {
    setStep(3);
    const refs = collectCheckedLeafIds(scopeNodes);
    // store for the plan effect
    // eslint-disable-next-line no-use-before-define
    _setSelectedRefs(refs);
  }

  const [selectedRefs, _setSelectedRefs] = useState(null);

  useEffect(() => {
    if (step !== 3 || !createdSource || selectedRefs === null) return;
    let cancelled = false;
    setPlanState("loading"); setRunError(null);
    planSource(createdSource.id, { selected_refs: selectedRefs })
      .then((data) => {
        if (cancelled) return;
        setPlanData(data);
        setIncludeText((data.plan.include ?? []).join(", "));
        setExcludeText((data.plan.exclude ?? []).join(", "));
        setPlanState("success");
      })
      .catch(() => { if (!cancelled) setPlanState("error"); });
    return () => { cancelled = true; };
  }, [step, createdSource, selectedRefs]);

  async function handleRunNow() {
    setRunSubmitting(true); setRunError(null);
    try {
      const run = await createRun(createdSource.id, {
        include: parsePatternList(includeText),
        exclude: parsePatternList(excludeText),
        size_cap_bytes: planData.plan.size_cap_bytes,
        budgets: planData.plan.budgets,
      });
      onRunStarted?.(run);
    } catch {
      setRunError("Could not start the run");
    } finally {
      setRunSubmitting(false);
    }
  }

  const filteredRepos = POPULAR_REPOS.filter((r) =>
    r.label.toLowerCase().includes(repoFilter.toLowerCase()) ||
    r.url.toLowerCase().includes(repoFilter.toLowerCase())
  );

  // ── render ────────────────────────────────────────────────────────────────

  return (
    <div data-testid="add-source-wizard" style={{ maxWidth: 760 }}>
      <StepIndicator steps={STEPS} active={step} />

      {/* ── STEP 0: Type ── */}
      {step === 0 && (
        <div data-testid="wizard-step-type">
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6, color: "var(--text-primary)" }}>
            What type of source do you want to add?
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 20 }}>
            Choose a source type. Only Git is available in this release; more coming soon.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            {SOURCE_TYPES.map((t) => (
              <button
                key={t.id}
                type="button"
                data-testid={`type-tile-${t.id}`}
                disabled={!t.enabled}
                onClick={() => t.enabled && selectType(t.id)}
                style={{
                  background: t.enabled ? "var(--bg-surface)" : "var(--bg-canvas)",
                  border: `2px solid ${t.enabled ? "#2563EB" : "var(--border-subtle)"}`,
                  borderRadius: 10, padding: "16px 14px", textAlign: "left",
                  cursor: t.enabled ? "pointer" : "not-allowed", opacity: t.enabled ? 1 : 0.5,
                }}
              >
                <div style={{ fontSize: 24, marginBottom: 6 }}>{t.icon}</div>
                <div style={{ fontWeight: 600, fontSize: 14, color: "var(--text-primary)", marginBottom: 2 }}>{t.label}</div>
                <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{t.description}</div>
                {!t.enabled && (
                  <div style={{ marginTop: 6, fontSize: 11, color: "var(--text-secondary)", fontStyle: "italic" }}>Coming soon</div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── STEP 1: Connect ── */}
      {step === 1 && (
        <div data-testid="wizard-step-connect">
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6, color: "var(--text-primary)" }}>
            Connect to your Git repository
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 20 }}>
            Enter the repository URL or pick from popular repos below.
          </p>

          <Card style={{ marginBottom: 16 }}>
            {/* URL field */}
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>
                Repository URL <span style={{ color: "#DC2626" }}>*</span>
              </label>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  data-testid="connect-uri-input"
                  type="text"
                  placeholder="https://github.com/owner/repo"
                  value={uri}
                  onChange={(e) => { setUri(e.target.value); setTestState("idle"); }}
                  style={inputStyle}
                />
                <button
                  type="button"
                  onClick={() => setShowRepoList((v) => !v)}
                  style={{
                    padding: "9px 16px", borderRadius: 8, border: "1px solid var(--border-subtle)",
                    background: showRepoList ? "#1e3a5f" : "var(--bg-canvas)", color: "var(--text-primary)",
                    fontWeight: 500, fontSize: 14, cursor: "pointer", whiteSpace: "nowrap",
                  }}
                >
                  📋 Browse repos
                </button>
              </div>

              {/* Repo picker dropdown */}
              {showRepoList && (
                <div style={{
                  border: "1px solid var(--border-subtle)", borderRadius: 8, background: "var(--bg-surface)",
                  boxShadow: "0 4px 12px rgba(0,0,0,.3)", marginTop: 4, maxHeight: 280, overflowY: "auto",
                }}>
                  <div style={{ padding: "10px 12px", borderBottom: "1px solid var(--border-subtle)" }}>
                    <input
                      type="search"
                      placeholder="Filter repos…"
                      value={repoFilter}
                      onChange={(e) => setRepoFilter(e.target.value)}
                      style={{ ...inputStyle, marginBottom: 0, fontSize: 13 }}
                    />
                  </div>
                  {filteredRepos.map((r) => (
                    <button
                      key={r.url}
                      type="button"
                      onClick={() => { setUri(r.url); setShowRepoList(false); setTestState("idle"); }}
                      style={{
                        display: "block", width: "100%", textAlign: "left",
                        padding: "10px 16px", border: "none", background: "transparent",
                        cursor: "pointer", fontSize: 13, borderBottom: "1px solid var(--border-subtle)",
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = "#1e3a5f"}
                      onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                    >
                      <div style={{ fontWeight: 500, color: "var(--text-primary)" }}>{r.label}</div>
                      <div style={{ color: "var(--text-secondary)", fontSize: 12, marginTop: 2 }}>{r.url}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Credentials */}
            <div style={{ marginBottom: 20 }}>
              <label style={labelStyle}>
                Personal Access Token{" "}
                <span style={{ color: "#6B7280", fontWeight: 400 }}>(optional for public repos)</span>
              </label>
              <input
                data-testid="connect-credentials-input"
                type="password"
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx  (leave blank for public repos)"
                value={credentialsInput}
                onChange={(e) => handleCredentialsChange(e.target.value)}
                style={inputStyle}
              />
              <InfoBox>
                <strong>Where do I get a token?</strong>
                <ul style={{ margin: "6px 0 0 16px", padding: 0 }}>
                  <li><strong>GitHub:</strong> Settings → Developer settings → Personal access tokens → Generate new token (classic) → select <code>repo</code> scope</li>
                  <li><strong>GitLab:</strong> User Settings → Access Tokens → select <code>read_repository</code></li>
                  <li><strong>Public repos</strong> (like GitHub public) → leave blank, no token needed</li>
                </ul>
              </InfoBox>
            </div>

            {/* Test connection feedback */}
            {testState === "loading" && <Skeleton shape="row" count={1} />}
            {testState === "success" && <SuccessBox message="Connection verified successfully" />}
            {testState === "error" && <ErrorBox message={testError} />}
            {submitError && <ErrorBox message={submitError} />}

            {/* Actions */}
            <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
              <PrimaryBtn
                onClick={handleTestConnection}
                disabled={!uri || testState === "loading"}
              >
                {testState === "loading" ? "Testing…" : "Test connection"}
              </PrimaryBtn>
              <PrimaryBtn
                onClick={handleAddSource}
                disabled={testState !== "success" || submitting}
                style={{ background: submitting || testState !== "success" ? "#6EE7B7" : "#059669" }}
              >
                {submitting ? "Adding…" : "Add source →"}
              </PrimaryBtn>
              <GhostBtn onClick={() => setStep(0)}>← Back</GhostBtn>
              <GhostBtn onClick={onCancel}>Cancel</GhostBtn>
            </div>
          </Card>
        </div>
      )}

      {/* ── STEP 2: Discover ── */}
      {step === 2 && (
        <div data-testid="wizard-step-discover">
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6, color: "#111827" }}>
            Select what to harvest
          </h2>
          <p style={{ color: "#6B7280", fontSize: 14, marginBottom: 20 }}>
            Check the branches, paths or files you want to index. Use "Select recommended" to pick the defaults.
          </p>
          <Card>
            <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
              <input
                data-testid="scope-search-input"
                type="search"
                placeholder="Search…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ ...inputStyle, flex: 1, marginBottom: 0 }}
              />
              <GhostBtn onClick={() => setScopeNodes((n) => selectAllLeaves(n))}>
                Select recommended
              </GhostBtn>
            </div>
            <ScopeTree
              state={scopeTreeRenderState}
              nodes={visibleScopeNodes}
              onToggle={(node) => setScopeNodes((n) => toggleTree(n, node.id))}
            />
            <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
              <PrimaryBtn
                onClick={handleGoToPlan}
                disabled={scopeState !== "success"}
              >
                Next: Plan →
              </PrimaryBtn>
              <GhostBtn onClick={onCancel}>Cancel</GhostBtn>
            </div>
          </Card>
        </div>
      )}

      {/* ── STEP 3: Plan & Run ── */}
      {step === 3 && (
        <div data-testid="wizard-step-plan">
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6, color: "#111827" }}>
            Review the harvest plan
          </h2>
          <p style={{ color: "#6B7280", fontSize: 14, marginBottom: 20 }}>
            Adjust include/exclude patterns if needed, then start the harvest.
          </p>
          <Card>
            <PlanSummaryCard
              state={planState === "idle" ? "loading" : planState}
              profile={planData?.profile}
              plan={{ include: parsePatternList(includeText), exclude: parsePatternList(excludeText) }}
              estimatedBytes={planData?.estimated_bytes}
              estimatedFiles={planData?.estimated_files}
              estimatedSeconds={planData?.estimated_seconds}
              estimatedTokens={planData?.estimated_tokens}
              budgetWarnings={planData?.budget_warnings}
            />
            {planState === "success" && (
              <div style={{ marginTop: 20 }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
                  <div>
                    <label style={labelStyle}>Include patterns <span style={{ color: "var(--text-secondary)", fontWeight: 400 }}>(comma-separated)</span></label>
                    <input
                      data-testid="plan-include-input"
                      type="text"
                      value={includeText}
                      onChange={(e) => setIncludeText(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Exclude patterns <span style={{ color: "var(--text-secondary)", fontWeight: 400 }}>(comma-separated)</span></label>
                    <input
                      data-testid="plan-exclude-input"
                      type="text"
                      value={excludeText}
                      onChange={(e) => setExcludeText(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                </div>
                {runError && <ErrorBox message={runError} />}
                <div style={{ display: "flex", gap: 10 }}>
                  <PrimaryBtn onClick={handleRunNow} disabled={runSubmitting} style={{ background: "#059669" }}>
                    {runSubmitting ? "Starting…" : "🚀 Run harvest now"}
                  </PrimaryBtn>
                  <GhostBtn onClick={onCancel}>Cancel</GhostBtn>
                </div>
              </div>
            )}
            {planState === "error" && <ErrorBox message="Could not load the harvest plan." />}
          </Card>
        </div>
      )}
    </div>
  );
}

const labelStyle = {
  display: "block", fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6,
};

const inputStyle = {
  width: "100%", padding: "9px 12px", border: "1px solid var(--border-subtle)", borderRadius: 8,
  fontSize: 14, color: "var(--text-primary)", outline: "none", boxSizing: "border-box", marginBottom: 0,
};
