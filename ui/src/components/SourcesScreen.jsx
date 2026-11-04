import { useEffect, useRef, useState } from "react";
import { listSources, runSource, deleteSource, getRun } from "../api.js";
import { AddSourceWizard } from "./AddSourceWizard.jsx";

const STATUS_COLOR = {
  active:   { bg: "#052e16", text: "#6EE7B7", dot: "#059669" },
  pending:  { bg: "#1c1a05", text: "#FCD34D", dot: "#F59E0B" },
  error:    { bg: "#3b0f0f", text: "#FCA5A5", dot: "#DC2626" },
  inactive: { bg: "#1e2130", text: "#9AA2B1", dot: "#4B5563" },
};

const RUN_STATE_COLOR = {
  CONNECTING:  "#6B7280", DISCOVERING: "#6B7280", PROFILING: "#6B7280", PLANNED: "#6B7280",
  APPROVED:    "#D97706", HARVESTING:  "#2563EB", VALIDATING: "#7C3AED",
  PUBLISHED:   "#059669", QUARANTINED: "#D97706", FAILED: "#DC2626", PARTIAL: "#D97706",
};

function StatusPill({ status }) {
  const c = STATUS_COLOR[status] ?? STATUS_COLOR.inactive;
  return (
    <span style={{ background: c.bg, color: c.text, borderRadius: 20, padding: "3px 10px", fontSize: 12, fontWeight: 600, display: "inline-flex", alignItems: "center", gap: 5 }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: c.dot, display: "inline-block" }} />
      {status}
    </span>
  );
}

function TypeIcon({ type }) {
  const icons = { git: "⎇", sql: "🗄", upload: "📄", snowflake: "❄", sharepoint: "🔗", tableau: "📊" };
  return <span style={{ fontSize: 18 }}>{icons[type] ?? "📁"}</span>;
}

function formatSchedule(schedule) {
  if (!schedule) return "Manual only";
  const map = { "@hourly": "Every hour", "@daily": "Daily", "@weekly": "Weekly", "@monthly": "Monthly" };
  return map[schedule] ?? schedule;
}

function formatElapsed(startedAt) {
  if (!startedAt) return null;
  const ms = Date.now() - new Date(startedAt).getTime();
  if (ms < 60000) return `${Math.round(ms / 1000)}s`;
  if (ms < 3600000) return `${Math.round(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
  return `${Math.floor(ms / 3600000)}h ${Math.round((ms % 3600000) / 60000)}m`;
}

// ── Background run panel ──────────────────────────────────────────────────────

function RunStateChip({ state }) {
  const color = RUN_STATE_COLOR[state] ?? "#6B7280";
  const isActive = !["PUBLISHED", "QUARANTINED", "FAILED", "PARTIAL"].includes(state);
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, background: color + "18", color, borderRadius: 20, padding: "3px 9px", fontSize: 11, fontWeight: 700 }}>
      {isActive && <span style={{ width: 7, height: 7, borderRadius: "50%", background: color, animation: "pulse 1.4s infinite" }} />}
      {state}
    </span>
  );
}

function BackgroundRunPanel({ bgRuns, onOpenFull, onDismiss }) {
  const [expanded, setExpanded] = useState(true);
  if (bgRuns.length === 0) return null;
  return (
    <div style={{ position: "fixed", bottom: 24, right: 24, width: 380, background: "#1E293B", borderRadius: 14, boxShadow: "0 8px 32px rgba(0,0,0,.3)", zIndex: 200, overflow: "hidden" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 16px", cursor: "pointer" }} onClick={() => setExpanded((v) => !v)}>
        <span style={{ fontSize: 14 }}>⚡</span>
        <span style={{ flex: 1, fontWeight: 700, fontSize: 13, color: "#F1F5F9" }}>Background harvests ({bgRuns.length})</span>
        <span style={{ fontSize: 13, color: "#94A3B8" }}>{expanded ? "▾" : "▴"}</span>
      </div>
      {expanded && bgRuns.map((r) => (
        <div key={r.runId} style={{ borderTop: "1px solid #334155", padding: "10px 16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "#CBD5E1" }}>{r.sourceName}</span>
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              {r.elapsed && <span style={{ fontSize: 11, color: "#64748B" }}>{r.elapsed}</span>}
              <RunStateChip state={r.state} />
            </div>
          </div>
          {/* Mini log — last 3 lines */}
          <div style={{ background: "#0F172A", borderRadius: 6, padding: "6px 10px", fontFamily: "monospace", fontSize: 10, color: "#7DD3FC", maxHeight: 60, overflow: "hidden" }}>
            {r.logLines.length === 0
              ? <span style={{ color: "#475569" }}>Waiting for log entries…</span>
              : r.logLines.slice(-3).map((l, i) => <div key={i} style={{ lineHeight: 1.6 }}>{l}</div>)
            }
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button type="button" onClick={() => onOpenFull(r.runId, r.runObj)}
              style={{ flex: 1, background: "#2563EB", color: "#fff", border: "none", borderRadius: 6, padding: "5px 0", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
              Full view →
            </button>
            {["PUBLISHED", "QUARANTINED", "FAILED", "PARTIAL"].includes(r.state) && (
              <button type="button" onClick={() => onDismiss(r.runId)}
                style={{ background: "#334155", color: "#94A3B8", border: "none", borderRadius: 6, padding: "5px 10px", fontSize: 11, cursor: "pointer" }}>
                Dismiss
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main screen ───────────────────────────────────────────────────────────────

export function SourcesScreen({ onRunStarted }) {
  const [state, setState] = useState("loading");
  const [sources, setSources] = useState([]);
  const [runningIds, setRunningIds] = useState(new Set());
  const [deletingIds, setDeletingIds] = useState(new Set());
  const [runError, setRunError] = useState(null);
  const [addingSource, setAddingSource] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [bgRuns, setBgRuns] = useState([]); // { runId, runObj, sourceName, state, logLines, elapsed, startedAt }
  const bgPollRef = useRef({});

  function loadSources() {
    return listSources()
      .then((rows) => { setSources(rows); setState(rows.length === 0 ? "empty" : "success"); })
      .catch(() => setState("error"));
  }

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    listSources()
      .then((rows) => { if (!cancelled) { setSources(rows); setState(rows.length === 0 ? "empty" : "success"); } })
      .catch(() => { if (!cancelled) setState("error"); });
    return () => { cancelled = true; };
  }, []);

  // Poll background runs
  useEffect(() => {
    const TERMINAL = ["PUBLISHED", "QUARANTINED", "FAILED", "PARTIAL"];
    const timers = {};
    function pollRun(runId) {
      if (!bgPollRef.current[runId]) return;
      getRun(runId).then((data) => {
        if (!bgPollRef.current[runId]) return;
        const logLines = (data.log_entries ?? []).map((e) => `${e.outcome ?? "→"} ${e.ref}`);
        setBgRuns((prev) => prev.map((r) =>
          r.runId === runId ? { ...r, state: data.state, logLines, elapsed: formatElapsed(data.started_at), runObj: data } : r
        ));
        if (!TERMINAL.includes(data.state)) {
          timers[runId] = setTimeout(() => pollRun(runId), 2000);
        }
      }).catch(() => {
        timers[runId] = setTimeout(() => pollRun(runId), 5000);
      });
    }
    bgRuns.forEach((r) => {
      if (!bgPollRef.current[r.runId]) {
        bgPollRef.current[r.runId] = true;
        pollRun(r.runId);
      }
    });
    return () => { Object.values(timers).forEach(clearTimeout); };
  }, [bgRuns.map((r) => r.runId).join(",")]);

  if (addingSource) {
    return (
      <AddSourceWizard
        onCancel={() => setAddingSource(false)}
        onSourceCreated={() => loadSources()}
        onRunStarted={(run) => { setAddingSource(false); onRunStarted(run); }}
      />
    );
  }

  async function handleRun(sourceId, background = false) {
    setRunError(null);
    setRunningIds((s) => new Set(s).add(sourceId));
    try {
      const run = await runSource(sourceId);
      if (background) {
        const src = sources.find((s) => s.id === sourceId);
        bgPollRef.current[run.id] = true;
        setBgRuns((prev) => [...prev, { runId: run.id, runObj: run, sourceName: src?.uri?.replace(/^https?:\/\/[^/]+\//, "") ?? sourceId, state: run.state ?? "APPROVED", logLines: [], elapsed: "0s", startedAt: new Date().toISOString() }]);
      } else {
        onRunStarted(run);
      }
    } catch (err) {
      setRunError(`Could not start a run: ${err.message}`);
    } finally {
      setRunningIds((s) => { const n = new Set(s); n.delete(sourceId); return n; });
    }
  }

  async function handleRunSelected(background = false) {
    for (const id of selectedIds) {
      await handleRun(id, background);
    }
    setSelectedIds(new Set());
  }

  async function handleDelete(sourceId) {
    if (!window.confirm("Remove this source? (It will be disabled and hidden from this list.)")) return;
    setDeletingIds((s) => new Set(s).add(sourceId));
    try {
      await deleteSource(sourceId);
      setSources((prev) => prev.filter((s) => s.id !== sourceId));
      setSelectedIds((prev) => { const n = new Set(prev); n.delete(sourceId); return n; });
      if (sources.length === 1) setState("empty");
    } catch {
      setRunError("Could not remove the source.");
    } finally {
      setDeletingIds((s) => { const n = new Set(s); n.delete(sourceId); return n; });
    }
  }

  function toggleSelect(id) {
    setSelectedIds((prev) => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }

  function toggleSelectAll() {
    const active = sources.filter((s) => s.status === "active").map((s) => s.id);
    if (active.every((id) => selectedIds.has(id))) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(active));
    }
  }

  function dismissBgRun(runId) {
    bgPollRef.current[runId] = false;
    setBgRuns((prev) => prev.filter((r) => r.runId !== runId));
  }

  // ── empty / error ────────────────────────────────────────────────────────────

  if (state === "loading") return <div style={{ padding: 24, color: "var(--text-secondary)" }}>Loading sources…</div>;
  if (state === "error")   return <div style={{ padding: 24, color: "var(--danger)" }}>Could not load sources. Check the API is running.</div>;

  if (state === "empty") {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 320, gap: 16, padding: 40 }}>
        <div style={{ fontSize: 48 }}>⎇</div>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>No sources yet</h2>
        <p style={{ color: "var(--text-secondary)", margin: 0 }}>Register a Git repo, database, or document store to start building your knowledge graph.</p>
        <button type="button" onClick={() => setAddingSource(true)} style={primaryBtnStyle}>
          + Add your first source
        </button>
      </div>
    );
  }

  // ── sources list ─────────────────────────────────────────────────────────────

  const activeSources = sources.filter((s) => s.status === "active");
  const allSelected = activeSources.length > 0 && activeSources.every((s) => selectedIds.has(s.id));
  const someSelected = selectedIds.size > 0;

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Sources</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: "4px 0 0" }}>{sources.length} source{sources.length !== 1 ? "s" : ""} registered</p>
        </div>
        <button type="button" onClick={() => setAddingSource(true)} style={primaryBtnStyle}>
          + Add source
        </button>
      </div>

      {/* Bulk action bar */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, padding: "10px 14px", background: someSelected ? "#1e3a5f" : "var(--bg-surface)", border: `1px solid ${someSelected ? "#2563EB44" : "var(--border-subtle)"}`, borderRadius: 10, transition: "all .2s" }}>
        <label style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 13, fontWeight: 600, color: "var(--text-primary)", cursor: "pointer" }}>
          <input type="checkbox" checked={allSelected} onChange={toggleSelectAll}
            style={{ width: 15, height: 15, accentColor: "#2563EB" }} />
          Select all active
        </label>
        {someSelected && (
          <>
            <span style={{ fontSize: 12, color: "#2563EB", fontWeight: 700 }}>{selectedIds.size} selected</span>
            <div style={{ display: "flex", gap: 8, marginLeft: "auto" }}>
              <button type="button" onClick={() => handleRunSelected(false)}
                style={{ background: "#059669", color: "#fff", border: "none", borderRadius: 7, padding: "6px 14px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                ▶ Run selected
              </button>
              <button type="button" onClick={() => handleRunSelected(true)}
                style={{ background: "#2563EB", color: "#fff", border: "none", borderRadius: 7, padding: "6px 14px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                ⚡ Run in background
              </button>
            </div>
          </>
        )}
      </div>

      {runError && (
        <div style={{ background: "#3b0f0f", border: "1px solid #DC262644", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#FCA5A5", marginBottom: 16 }}>
          {runError}
        </div>
      )}

      {/* Cards grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 16 }}>
        {sources.map((source) => {
          const isRunning = runningIds.has(source.id);
          const isDeleting = deletingIds.has(source.id);
          const isSelected = selectedIds.has(source.id);
          const repoName = source.uri?.replace(/^https?:\/\/[^/]+\//, "") ?? source.uri;
          const host = (() => { try { return new URL(source.uri).hostname; } catch { return ""; } })();
          const bgRun = bgRuns.find((r) => r.sourceName === repoName || r.runObj?.source_id === source.id);
          const lastHarvest = source.last_harvest_at ? new Date(source.last_harvest_at).toLocaleString() : null;

          return (
            <div key={source.id} data-testid={`source-row-${source.id}`}
              style={{ background: "var(--bg-surface)", border: `2px solid ${isSelected ? "#2563EB" : "var(--border-subtle)"}`, borderRadius: 12, padding: "20px 20px 16px", boxShadow: "0 1px 3px rgba(0,0,0,.05)", display: "flex", flexDirection: "column", gap: 12 }}>

              {/* Top row */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  {source.status === "active" && (
                    <input type="checkbox" checked={isSelected} onChange={() => toggleSelect(source.id)}
                      style={{ width: 15, height: 15, accentColor: "#2563EB", cursor: "pointer", flexShrink: 0 }} />
                  )}
                  <div style={{ width: 36, height: 36, background: "#1e3a5f", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <TypeIcon type={source.type} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "var(--text-primary)", lineHeight: 1.3 }}>{repoName}</div>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{host}</div>
                  </div>
                </div>
                <StatusPill status={source.status} />
              </div>

              {/* URI */}
              <a href={source.uri} target="_blank" rel="noopener noreferrer"
                style={{ fontSize: 12, color: "#2563EB", textDecoration: "none", wordBreak: "break-all" }}>
                {source.uri}
              </a>

              {/* Meta row */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 12px", fontSize: 12, color: "var(--text-secondary)" }}>
                <span>Type: <strong style={{ color: "var(--text-primary)" }}>{source.type}</strong></span>
                <span>Owner: <strong style={{ color: "var(--text-primary)" }}>{source.owner ?? "—"}</strong></span>
                <span>Schedule: <strong style={{ color: "var(--text-primary)" }}>{formatSchedule(source.schedule)}</strong></span>
                {lastHarvest && <span>Last run: <strong style={{ color: "var(--text-primary)" }}>{lastHarvest}</strong></span>}
              </div>

              {/* Background run status strip */}
              {bgRun && (
                <div style={{ display: "flex", alignItems: "center", gap: 8, background: "#0F172A", borderRadius: 8, padding: "7px 10px" }}>
                  <span style={{ width: 7, height: 7, borderRadius: "50%", background: RUN_STATE_COLOR[bgRun.state] ?? "#6B7280", flexShrink: 0 }} />
                  <span style={{ fontSize: 11, color: "#7DD3FC", fontFamily: "monospace", flex: 1 }}>
                    {bgRun.logLines[bgRun.logLines.length - 1] ?? "Waiting…"}
                  </span>
                  <RunStateChip state={bgRun.state} />
                  {bgRun.elapsed && <span style={{ fontSize: 10, color: "#475569" }}>{bgRun.elapsed}</span>}
                </div>
              )}

              {/* Footer */}
              <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: 12, display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap" }}>
                {source.status === "active" && (
                  <>
                    <button type="button" onClick={() => handleRun(source.id, false)} disabled={isRunning || isDeleting}
                      style={{ background: isRunning ? "#6EE7B7" : "#059669", color: "#fff", border: "none", borderRadius: 7, padding: "7px 14px", fontSize: 12, fontWeight: 600, cursor: isRunning ? "not-allowed" : "pointer" }}>
                      {isRunning ? "Starting…" : "▶ Run now"}
                    </button>
                    <button type="button" onClick={() => handleRun(source.id, true)} disabled={isRunning || isDeleting}
                      style={{ background: "#2563EB", color: "#fff", border: "none", borderRadius: 7, padding: "7px 14px", fontSize: 12, fontWeight: 600, cursor: isRunning ? "not-allowed" : "pointer" }}>
                      ⚡ Background
                    </button>
                  </>
                )}
                <button type="button" onClick={() => handleDelete(source.id)} disabled={isDeleting}
                  style={{ background: "transparent", color: "var(--danger)", border: "1px solid var(--danger)", borderRadius: 7, padding: "7px 12px", fontSize: 12, fontWeight: 600, cursor: isDeleting ? "not-allowed" : "pointer", opacity: 0.8 }}>
                  {isDeleting ? "Removing…" : "✕ Remove"}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Background run floating panel */}
      <BackgroundRunPanel
        bgRuns={bgRuns}
        onOpenFull={(runId, runObj) => { onRunStarted(runObj); }}
        onDismiss={dismissBgRun}
      />

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }`}</style>
    </div>
  );
}

const primaryBtnStyle = {
  background: "#2563EB", color: "#fff", border: "none", borderRadius: 8,
  padding: "9px 20px", fontWeight: 600, fontSize: 14, cursor: "pointer",
};
