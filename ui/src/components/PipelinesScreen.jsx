import { useEffect, useState } from "react";
import { extractOntology, listSources, listSourceRuns, normalizeRun, runSource } from "../api.js";

const STATE_COLOR = {
  PUBLISHED:   "#059669",
  HARVESTING:  "#2563EB",
  VALIDATING:  "#7C3AED",
  APPROVED:    "#6B7280",
  QUARANTINED: "#D97706",
  PARTIAL:     "#D97706",
  FAILED:      "#DC2626",
  CONNECTING:  "#6B7280",
  DISCOVERING: "#6B7280",
  PROFILING:   "#6B7280",
  PLANNED:     "#6B7280",
};

const TERMINAL = new Set(["PUBLISHED", "QUARANTINED", "FAILED", "PARTIAL"]);

function stateDot(state) {
  const color = STATE_COLOR[state] ?? "#6B7280";
  const pulse = !TERMINAL.has(state) && state !== undefined;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
      <span style={{
        display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: color,
        boxShadow: pulse ? `0 0 0 3px ${color}33` : "none",
      }} />
      <span style={{ fontSize: 11, fontWeight: 600, color }}>{state ?? "—"}</span>
    </span>
  );
}

function PipelineStep({ num, label, done, running, disabled, onRun, result }) {
  const bg = done ? "#064E3B22" : running ? "#1e3a5f33" : "var(--bg-canvas)";
  const border = done ? "#059669" : running ? "#2563EB" : "var(--border-subtle)";
  const circleColor = done ? "#059669" : running ? "#2563EB" : num === 3 ? "#7C3AED" : "#334155";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", borderRadius: 8, border: `1px solid ${border}`, background: bg, opacity: disabled ? 0.4 : 1 }}>
      <div style={{ width: 22, height: 22, borderRadius: "50%", background: circleColor, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 11, color: "#fff", flexShrink: 0 }}>
        {done ? "✓" : num}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)" }}>{label}</div>
        {result && <div style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{result}</div>}
      </div>
      {!done && !disabled && onRun && (
        <button type="button" onClick={onRun} disabled={running}
          style={{ fontSize: 10, fontWeight: 700, background: running ? "#334155" : num === 3 ? "#7C3AED" : "#2563EB", color: "#fff", border: "none", borderRadius: 5, padding: "4px 10px", cursor: running ? "not-allowed" : "pointer", flexShrink: 0 }}>
          {running ? "…" : "▶"}
        </button>
      )}
    </div>
  );
}

function describeCron(cron) {
  const presets = {
    "0 * * * *": "Every hour",
    "0 0 * * *": "Daily at midnight",
    "0 6 * * *": "Daily at 6am",
    "0 0 * * 0": "Weekly (Sunday)",
    "0 0 1 * *": "Monthly",
  };
  return presets[cron] ?? cron;
}

function SourcePipelineCard({ source, onViewRun }) {
  const [latestRun, setLatestRun] = useState(null);
  const [loadingRun, setLoadingRun] = useState(true);
  const [scheduleEnabled, setScheduleEnabled] = useState(!!source.schedule && source.schedule !== "manual");
  const [scheduleCron, setScheduleCron] = useState(source.schedule ?? "0 0 * * *");
  const [editingSchedule, setEditingSchedule] = useState(false);

  // Per-step state
  const [harvesting, setHarvesting] = useState(false);
  const [harvestRunId, setHarvestRunId] = useState(null);

  const [normalizing, setNormalizing] = useState(false);
  const [normalizeResult, setNormalizeResult] = useState(null);

  const [extracting, setExtracting] = useState(false);
  const [extractResult, setExtractResult] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const runs = await listSourceRuns(source.id, 1);
        if (!cancelled) setLatestRun(runs[0] ?? null);
      } catch (_) {}
      if (!cancelled) setLoadingRun(false);
    }
    load();
    return () => { cancelled = true; };
  }, [source.id]);

  // Poll while run is active
  useEffect(() => {
    if (!latestRun || TERMINAL.has(latestRun.state)) return;
    const timer = setInterval(async () => {
      try {
        const runs = await listSourceRuns(source.id, 1);
        setLatestRun(runs[0] ?? null);
      } catch (_) {}
    }, 2500);
    return () => clearInterval(timer);
  }, [latestRun, source.id]);

  async function handleHarvest() {
    setHarvesting(true);
    try {
      const run = await runSource(source.id);
      setLatestRun(run);
      setHarvestRunId(run.id);
    } catch (_) {}
    setHarvesting(false);
  }

  async function handleNormalize() {
    const rid = latestRun?.id;
    if (!rid) return;
    setNormalizing(true);
    try {
      const r = await normalizeRun(rid);
      setNormalizeResult(r.message ?? "Done");
    } catch (e) { setNormalizeResult("Error: " + e.message); }
    setNormalizing(false);
  }

  async function handleExtract() {
    setExtracting(true);
    try {
      const r = await extractOntology();
      setExtractResult(`${r.edges_created} edges`);
    } catch (e) { setExtractResult("Error: " + e.message); }
    setExtracting(false);
  }

  const isPublished = latestRun?.state === "PUBLISHED";
  const isActive = latestRun && !TERMINAL.has(latestRun.state);

  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 12, padding: "16px 18px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 14 }}>
        <div style={{ width: 36, height: 36, borderRadius: 10, background: "#1e3a5f", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>
          {source.type === "git" ? "⎇" : "📄"}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {source.uri.split("/").slice(-2).join("/")}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>{source.type} · {source.owner ?? "—"}</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          {loadingRun ? null : stateDot(latestRun?.state)}
          {latestRun && (
            <button type="button" onClick={() => onViewRun(latestRun.id)}
              style={{ fontSize: 10, fontWeight: 600, background: "var(--bg-canvas)", border: "1px solid var(--border-subtle)", borderRadius: 5, padding: "3px 8px", color: "var(--text-secondary)", cursor: "pointer" }}>
              View →
            </button>
          )}
        </div>
      </div>

      {/* Pipeline steps */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <PipelineStep
          num={1} label="Harvest"
          done={isPublished}
          running={harvesting || isActive}
          onRun={handleHarvest}
          result={isPublished ? `Run ${latestRun.id.slice(0, 8)}…` : null}
        />
        <PipelineStep
          num={2} label="Normalize source"
          done={!!normalizeResult}
          running={normalizing}
          disabled={!isPublished}
          onRun={handleNormalize}
          result={normalizeResult}
        />
        <PipelineStep
          num={3} label="Build Ontology (all sources)"
          done={!!extractResult}
          running={extracting}
          disabled={!normalizeResult}
          onRun={handleExtract}
          result={extractResult}
        />
      </div>

      {/* Scheduler */}
      <div style={{ marginTop: 12, borderTop: "1px solid var(--border-subtle)", paddingTop: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: editingSchedule ? 8 : 0 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", flex: 1 }}>Schedule</span>
          <div onClick={() => setScheduleEnabled(v => !v)} style={{ width: 36, height: 20, borderRadius: 10, background: scheduleEnabled ? "#2563EB" : "#334155", cursor: "pointer", position: "relative", transition: "background .2s", flexShrink: 0 }}>
            <div style={{ position: "absolute", top: 2, left: scheduleEnabled ? 18 : 2, width: 16, height: 16, borderRadius: "50%", background: "#fff", transition: "left .2s" }} />
          </div>
          {scheduleEnabled && !editingSchedule && (
            <span style={{ fontSize: 11, color: "var(--text-secondary)", cursor: "pointer" }} onClick={() => setEditingSchedule(true)}>
              {describeCron(scheduleCron)} ✎
            </span>
          )}
        </div>
        {scheduleEnabled && editingSchedule && (
          <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
            <input value={scheduleCron} onChange={e => setScheduleCron(e.target.value)}
              placeholder="cron expression"
              style={{ flex: 1, background: "var(--bg-canvas)", border: "1px solid var(--border-subtle)", borderRadius: 6, padding: "5px 8px", color: "var(--text-primary)", fontSize: 12, fontFamily: "monospace", outline: "none" }} />
            <button type="button" onClick={() => setEditingSchedule(false)}
              style={{ background: "#2563EB", color: "#fff", border: "none", borderRadius: 6, padding: "5px 10px", fontSize: 12, cursor: "pointer", fontWeight: 600 }}>Save</button>
            <button type="button" onClick={() => setEditingSchedule(false)}
              style={{ background: "var(--bg-canvas)", color: "var(--text-secondary)", border: "1px solid var(--border-subtle)", borderRadius: 6, padding: "5px 10px", fontSize: 12, cursor: "pointer" }}>✕</button>
          </div>
        )}
        {!scheduleEnabled && <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>Manual only</div>}
      </div>
    </div>
  );
}

export function PipelinesScreen({ onViewRun }) {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    listSources()
      .then(setSources)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: "var(--text-secondary)", padding: 32 }}>Loading…</div>;
  if (error) return <div style={{ color: "var(--danger)", padding: 32 }}>{error}</div>;

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Pipelines</h2>
          <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>
            Harvest → Normalize → Build Ontology for each registered source
          </div>
        </div>
        <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{sources.length} sources</div>
      </div>

      {sources.length === 0 ? (
        <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-secondary)" }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>📭</div>
          <div style={{ fontWeight: 600 }}>No sources yet</div>
          <div style={{ fontSize: 13, marginTop: 4 }}>Add a source in the Sources screen to get started.</div>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 16 }}>
          {sources.map((s) => (
            <SourcePipelineCard key={s.id} source={s} onViewRun={onViewRun} />
          ))}
        </div>
      )}
    </div>
  );
}
