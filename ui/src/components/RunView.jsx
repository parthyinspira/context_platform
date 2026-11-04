import { useEffect, useRef, useState } from "react";
import { extractOntology, getRun, normalizeRun, stopRun } from "../api.js";

const POLL_INTERVAL_MS = 2000;
const TERMINAL_STATES = ["PUBLISHED", "QUARANTINED", "FAILED", "PARTIAL"];
const TERMINAL_FAILURE_STATES = ["QUARANTINED", "FAILED", "PARTIAL"];
const REPORT_STATES = ["PUBLISHED", "QUARANTINED", "PARTIAL"];

const STAGE_ORDER = [
  "CONNECTING", "DISCOVERING", "PROFILING", "PLANNED",
  "APPROVED", "HARVESTING", "VALIDATING", "PUBLISHED",
];

const STATE_META = {
  PUBLISHED:   { color: "#059669", bg: "#ECFDF5", label: "Published" },
  QUARANTINED: { color: "#D97706", bg: "#FFFBEB", label: "Quarantined" },
  PARTIAL:     { color: "#D97706", bg: "#FFFBEB", label: "Partial" },
  FAILED:      { color: "#DC2626", bg: "#FEF2F2", label: "Failed" },
  HARVESTING:  { color: "#2563EB", bg: "#EFF6FF", label: "Harvesting…" },
  VALIDATING:  { color: "#7C3AED", bg: "#F5F3FF", label: "Validating…" },
  APPROVED:    { color: "#6B7280", bg: "#F3F4F6", label: "Waiting to start…" },
  default:     { color: "#6B7280", bg: "#F3F4F6", label: "In progress…" },
};

function statusMeta(state) { return STATE_META[state] ?? STATE_META.default; }

function formatDuration(startedAt, endedAt) {
  if (!startedAt) return null;
  const ms = (endedAt ? new Date(endedAt) : new Date()) - new Date(startedAt);
  if (ms < 1000) return "<1s";
  if (ms < 60000) return `${Math.round(ms / 1000)}s`;
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
  return `${Math.floor(ms / 3600000)}h ${Math.round((ms % 3600000) / 60000)}m`;
}

// ── Stage progress bar ────────────────────────────────────────────────────────

function StageBar({ state }) {
  const isFailure = TERMINAL_FAILURE_STATES.includes(state);
  const idx = isFailure ? STAGE_ORDER.length - 1 : STAGE_ORDER.indexOf(state);
  const effectiveIdx = idx === -1 ? 0 : idx;

  return (
    <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", rowGap: 8 }}>
      {STAGE_ORDER.map((name, i) => {
        const done = i < effectiveIdx;
        const active = i === effectiveIdx;
        const failed = isFailure && active;
        const color = failed ? "#DC2626" : active ? "#2563EB" : done ? "#059669" : "#D1D5DB";

        return (
          <div key={name} style={{ display: "flex", alignItems: "center" }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", background: color, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: (done || active) ? "#fff" : "#9CA3AF", boxShadow: active ? `0 0 0 3px ${color}33` : "none", transition: "all .3s" }}>
              {done ? "✓" : failed ? "✕" : i + 1}
            </div>
            <div style={{ fontSize: 10, color: active ? "#111827" : done ? "#059669" : "#9CA3AF", fontWeight: active ? 700 : 400, margin: "0 4px", whiteSpace: "nowrap" }}>
              {name}
            </div>
            {i < STAGE_ORDER.length - 1 && (
              <div style={{ width: 20, height: 2, background: done ? "#059669" : "#E5E7EB", marginRight: 4 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Metric tile ───────────────────────────────────────────────────────────────

function MetricTile({ label, value, budget, unit = "" }) {
  const hasData = value != null;
  const hasBudget = budget != null;
  const pct = hasBudget && budget > 0 ? Math.min(100, Math.round((value / budget) * 100)) : null;

  return (
    <div style={{ background: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: 10, padding: "14px 16px", display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ fontSize: 11, color: "#6B7280", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".05em" }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: hasData ? "#111827" : "#D1D5DB" }}>
        {hasData ? `${value.toLocaleString()}${unit}` : "—"}
      </div>
      {hasBudget ? (
        <div style={{ fontSize: 11, color: "#6B7280" }}>
          Budget: {budget.toLocaleString()}{unit}
          {pct != null && (
            <div style={{ marginTop: 4, height: 4, background: "#E5E7EB", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${pct}%`, background: pct > 90 ? "#DC2626" : "#2563EB", borderRadius: 4 }} />
            </div>
          )}
        </div>
      ) : (
        <div style={{ fontSize: 11, color: "#D1D5DB" }}>No budget set</div>
      )}
    </div>
  );
}

// ── Live log sidebar ──────────────────────────────────────────────────────────

const OUTCOME_COLOR = {
  fetched: "#6EE7B7", skipped: "#64748B", failed: "#F87171", discovered: "#7DD3FC",
};

function LiveLog({ entries, isTerminal }) {
  const bottomRef = useRef(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries?.length]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", borderBottom: "1px solid #1E293B" }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: "#CBD5E1" }}>Live log</span>
        {!isTerminal && (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 10, color: "#7DD3FC" }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#7DD3FC", animation: "pulse 1.4s infinite" }} />
            streaming
          </span>
        )}
        {entries?.length > 0 && <span style={{ fontSize: 10, color: "#475569" }}>{entries.length} entries</span>}
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "8px 0", fontFamily: "monospace", fontSize: 11 }}>
        {(!entries || entries.length === 0) ? (
          <div style={{ padding: "20px 14px", color: "#475569", textAlign: "center" }}>
            {isTerminal ? "No log entries." : "Waiting for first entry…"}
          </div>
        ) : (
          entries.map((e, i) => (
            <div key={i} style={{ display: "flex", gap: 8, padding: "3px 14px", borderBottom: "1px solid #0F172A" }}>
              <span style={{ color: OUTCOME_COLOR[e.outcome] ?? "#94A3B8", fontWeight: 700, flexShrink: 0, fontSize: 10 }}>
                {(e.outcome ?? "→").toUpperCase()}
              </span>
              <span style={{ color: "#CBD5E1", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={e.ref}>
                {e.ref}
              </span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }`}</style>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function RunView({ run, onViewValidationReport, onBackToSources }) {
  const [detail, setDetail] = useState(null);
  const [loadError, setLoadError] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [stopError, setStopError] = useState(null);
  const [normalizing, setNormalizing] = useState(false);
  const [normalizeResult, setNormalizeResult] = useState(null);
  const [normalizeError, setNormalizeError] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [extractResult, setExtractResult] = useState(null);
  const [extractError, setExtractError] = useState(null);
  const [elapsed, setElapsed] = useState(null);
  const elapsedRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    let timer;
    function poll() {
      getRun(run.id)
        .then((data) => {
          if (cancelled) return;
          setDetail(data);
          setLoadError(false);
          if (!TERMINAL_STATES.includes(data.state)) {
            timer = setTimeout(poll, POLL_INTERVAL_MS);
          }
        })
        .catch(() => { if (!cancelled) setLoadError(true); });
    }
    poll();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [run.id]);

  // Elapsed time ticker
  useEffect(() => {
    if (!detail?.started_at) return;
    if (TERMINAL_STATES.includes(detail.state)) {
      setElapsed(formatDuration(detail.started_at, detail.updated_at));
      return;
    }
    function tick() { setElapsed(formatDuration(detail.started_at)); }
    tick();
    elapsedRef.current = setInterval(tick, 1000);
    return () => clearInterval(elapsedRef.current);
  }, [detail?.started_at, detail?.state, detail?.updated_at]);

  async function handleExtract() {
    setExtracting(true); setExtractError(null); setExtractResult(null);
    try {
      const r = await extractOntology();
      setExtractResult(r);
    } catch (e) { setExtractError(e.message); }
    finally { setExtracting(false); }
  }

  async function handleNormalize() {
    setNormalizing(true); setNormalizeError(null); setNormalizeResult(null);
    try {
      const r = await normalizeRun(detail.id);
      setNormalizeResult(r);
    } catch (err) {
      setNormalizeError(err.message);
    } finally {
      setNormalizing(false);
    }
  }

  async function handleStop() {
    setStopping(true); setStopError(null);
    try { const updated = await stopRun(run.id); setDetail(updated); }
    catch { setStopError("Could not stop the run"); }
    finally { setStopping(false); }
  }

  if (!detail) {
    return (
      <div data-testid="run-view" style={{ padding: 24, color: "#6B7280" }}>
        {loadError ? "Could not load run status — check the API is running." : "Loading run…"}
      </div>
    );
  }

  const isTerminal = TERMINAL_STATES.includes(detail.state);
  const meta = statusMeta(detail.state);
  const budgets = detail.plan?.budgets ?? {};
  const manifest = detail.manifest_summary ?? {};

  return (
    <div data-testid="run-view" style={{ display: "flex", gap: 20, maxWidth: 1200 }}>
      {/* ── Main column ── */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: "#111827", margin: 0 }}>Harvest Run</h1>
            <div style={{ fontSize: 12, color: "#9CA3AF", marginTop: 4, fontFamily: "monospace" }}>{detail.id}</div>
            {elapsed && (
              <div style={{ fontSize: 12, color: "#6B7280", marginTop: 4 }}>
                ⏱ {isTerminal ? `Completed in ${elapsed}` : `Running for ${elapsed}`}
                {detail.started_at && <span style={{ color: "#D1D5DB", marginLeft: 8 }}>· started {new Date(detail.started_at).toLocaleTimeString()}</span>}
              </div>
            )}
          </div>
          <span style={{ background: meta.bg, color: meta.color, borderRadius: 20, padding: "5px 14px", fontSize: 13, fontWeight: 700 }}>
            {meta.label}
          </span>
        </div>

        {/* Stage bar */}
        <div style={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: 12, padding: "20px 24px", marginBottom: 16, overflowX: "auto" }}>
          <StageBar state={detail.state} />
        </div>

        {/* Metrics */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 10, marginBottom: 16 }}>
          <MetricTile label="Files"      value={manifest.fetched}       budget={budgets.max_files} />
          <MetricTile label="Bytes"      value={manifest.fetched_bytes} budget={budgets.max_bytes} />
          <MetricTile label="Discovered" value={manifest.discovered} />
          <MetricTile label="Skipped"    value={manifest.skipped} />
          <MetricTile label="Failed"     value={manifest.failed} />
        </div>

        {/* Two-step pipeline after PUBLISHED */}
        {detail.state === "PUBLISHED" && (
          <div style={{ background: "#0F172A", border: "1px solid #1E293B", borderRadius: 12, padding: "16px 20px", marginBottom: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#64748B", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 14 }}>
              Knowledge pipeline
            </div>

            {/* Step 1: Normalize */}
            <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12, padding: "12px 14px", background: normalizeResult ? "#064E3B22" : "#1E293B", borderRadius: 10, border: `1px solid ${normalizeResult ? "#059669" : "#334155"}` }}>
              <div style={{ width: 28, height: 28, borderRadius: "50%", background: normalizeResult ? "#059669" : "#2563EB", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 13, color: "#fff", flexShrink: 0 }}>
                {normalizeResult ? "✓" : "1"}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#E2E8F0" }}>Normalize source</div>
                <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>
                  {normalizeResult ? normalizeResult.message : "Create entity-per-file within this source (Repository → Modules, Tables, Documents)"}
                </div>
              </div>
              {!normalizeResult && (
                <button type="button" onClick={handleNormalize} disabled={normalizing}
                  style={{ background: normalizing ? "#334155" : "#2563EB", color: "#fff", border: "none", borderRadius: 7, padding: "7px 16px", fontWeight: 700, fontSize: 12, cursor: normalizing ? "not-allowed" : "pointer", flexShrink: 0 }}>
                  {normalizing ? "Running…" : "▶ Run"}
                </button>
              )}
            </div>

            {/* Step 2: Ontology */}
            <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 14px", background: extractResult ? "#1a0e3a" : "#1E293B", borderRadius: 10, border: `1px solid ${extractResult ? "#7C3AED" : "#334155"}`, opacity: normalizeResult ? 1 : 0.5 }}>
              <div style={{ width: 28, height: 28, borderRadius: "50%", background: extractResult ? "#7C3AED" : "#6D28D9", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 13, color: "#fff", flexShrink: 0 }}>
                {extractResult ? "✓" : "2"}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#E2E8F0" }}>Build Ontology</div>
                <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>
                  {extractResult ? extractResult.message : "Cross-source SQL analysis + import parsing → READS_FROM / WRITES_TO / DEPENDS_ON edges"}
                </div>
              </div>
              {!extractResult && (
                <button type="button" onClick={handleExtract} disabled={extracting || !normalizeResult}
                  style={{ background: extracting ? "#334155" : "#7C3AED", color: "#fff", border: "none", borderRadius: 7, padding: "7px 16px", fontWeight: 700, fontSize: 12, cursor: (extracting || !normalizeResult) ? "not-allowed" : "pointer", flexShrink: 0 }}>
                  {extracting ? "Running…" : "▶ Run"}
                </button>
              )}
            </div>

            {normalizeError && <div style={{ color: "#F87171", fontSize: 12, marginTop: 8 }}>{normalizeError}</div>}
            {extractError && <div style={{ color: "#F87171", fontSize: 12, marginTop: 4 }}>{extractError}</div>}
          </div>
        )}

        {/* Error / stop error */}
        {detail.error && (
          <div style={{ background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: 10, padding: "12px 16px", color: "#DC2626", fontSize: 13, marginBottom: 16 }}>
            <strong>Error:</strong> {detail.error}
          </div>
        )}
        {stopError && (
          <div style={{ background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: 10, padding: "12px 16px", color: "#DC2626", fontSize: 13, marginBottom: 16 }}>
            {stopError}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", gap: 12 }}>
          {!isTerminal && (
            <button type="button" data-testid="stop-run-button" disabled={stopping} onClick={handleStop}
              style={{ background: stopping ? "#FCA5A5" : "#DC2626", color: "#fff", border: "none", borderRadius: 8, padding: "9px 20px", fontWeight: 600, fontSize: 14, cursor: stopping ? "not-allowed" : "pointer" }}>
              {stopping ? "Stopping…" : "⏹ Stop run"}
            </button>
          )}
          {isTerminal && REPORT_STATES.includes(detail.state) && (
            <button type="button" data-testid="view-validation-report-link" onClick={() => onViewValidationReport?.(detail.id)}
              style={{ background: "#2563EB", color: "#fff", border: "none", borderRadius: 8, padding: "9px 20px", fontWeight: 600, fontSize: 14, cursor: "pointer" }}>
              View validation report →
            </button>
          )}
          <button type="button" data-testid="back-to-sources-link" onClick={onBackToSources}
            style={{ background: "transparent", color: "#6B7280", border: "1px solid #E5E7EB", borderRadius: 8, padding: "9px 20px", fontWeight: 600, fontSize: 14, cursor: "pointer" }}>
            ← Back to sources
          </button>
        </div>
      </div>

      {/* ── Live log sidebar ── */}
      <div style={{ width: 300, flexShrink: 0, background: "#1E293B", borderRadius: 12, overflow: "hidden", display: "flex", flexDirection: "column", minHeight: 400 }}>
        <LiveLog entries={detail.log_entries} isTerminal={isTerminal} />
      </div>
    </div>
  );
}
