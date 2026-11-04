import { useCallback, useEffect, useState } from "react";
import { extractOntology, getGraph, listSources } from "../api.js";
import { GraphCanvas } from "./GraphCanvas.jsx";
import { EmptyState } from "./EmptyState.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";

const TYPE_ICONS = {
  Repository: "⎇", Module: "🧩", Document: "📄", Table: "🗄️",
  Job: "⚙️", Dashboard: "📊", Service: "🔌", Person: "👤", Team: "👥", Column: "🔑",
};

const RELATION_COLORS = {
  CONTAINS: "#3B82F6", DEPENDS_ON: "#F59E0B", DOCUMENTS: "#10B981",
  READS_FROM: "#8B5CF6", WRITES_TO: "#EF4444", DERIVED_FROM: "#EC4899",
  OWNED_BY: "#6B7280",
};

function SourceFilterPanel({ sources, activeIds, onToggle, onToggleAll, graph }) {
  const countFor = (sid) => graph.nodes.filter((n) => n.source_id === sid).length;

  return (
    <div style={{ width: 220, flexShrink: 0, background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 12, padding: "14px 0", display: "flex", flexDirection: "column", overflow: "hidden", minHeight: 0 }}>
      <div style={{ padding: "0 14px 10px", borderBottom: "1px solid var(--border-subtle)" }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 8 }}>
          Sources
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12, color: "var(--text-secondary)", cursor: "pointer" }}>
          <input type="checkbox"
            checked={sources.length > 0 && sources.every((s) => activeIds.has(s.id))}
            onChange={onToggleAll}
            style={{ accentColor: "#2563EB" }} />
          Show all sources
        </label>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
        {sources.length === 0 && (
          <div style={{ padding: "12px 14px", fontSize: 12, color: "var(--text-secondary)" }}>No sources yet</div>
        )}
        {sources.map((s) => {
          const on = activeIds.has(s.id);
          const name = s.uri?.split("/").slice(-1)[0] ?? s.uri;
          const count = countFor(s.id);
          return (
            <div key={s.id} onClick={() => onToggle(s.id)}
              style={{ display: "flex", alignItems: "center", gap: 9, padding: "8px 14px", cursor: "pointer", background: on ? "#2563EB22" : "transparent", borderLeft: `3px solid ${on ? "#2563EB" : "transparent"}` }}>
              <input type="checkbox" checked={on} onChange={() => onToggle(s.id)}
                style={{ accentColor: "#2563EB", cursor: "pointer" }} onClick={(e) => e.stopPropagation()} />
              <span style={{ fontSize: 16 }}>{TYPE_ICONS.Repository}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {name}
                </div>
                <div style={{ fontSize: 10, color: "var(--text-secondary)" }}>{s.type} · {count} entities</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Entity type legend */}
      <div style={{ borderTop: "1px solid var(--border-subtle)", padding: "10px 14px 0" }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 8 }}>Entity types</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {Object.entries(TYPE_ICONS).map(([t, icon]) => {
            const count = graph.nodes.filter((n) => n.type === t).length;
            if (count === 0) return null;
            return (
              <div key={t} style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 11 }}>
                <span style={{ fontSize: 13 }}>{icon}</span>
                <span style={{ flex: 1, color: "var(--text-secondary)" }}>{t}</span>
                <span style={{ color: "var(--text-secondary)", fontFamily: "monospace" }}>{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Relation legend */}
      {graph.edges.length > 0 && (
        <div style={{ borderTop: "1px solid #334155", padding: "10px 14px", marginTop: 8 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "#64748B", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 8 }}>Relations</div>
          {[...new Set(graph.edges.map((e) => e.relation))].map((r) => (
            <div key={r} style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 11, marginBottom: 4 }}>
              <div style={{ width: 24, height: 2, background: RELATION_COLORS[r] ?? "#64748B", borderRadius: 1 }} />
              <span style={{ color: "#94A3B8", fontFamily: "monospace" }}>{r}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function GraphStats({ graph }) {
  const byType = {};
  graph.nodes.forEach((n) => { byType[n.type] = (byType[n.type] ?? 0) + 1; });
  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 10 }}>
      {Object.entries(byType).map(([t, c]) => (
        <span key={t} style={{ fontSize: 11, background: "#1E293B", color: "#94A3B8", borderRadius: 20, padding: "3px 10px" }}>
          {TYPE_ICONS[t] ?? "🔵"} {t} <strong style={{ color: "#E2E8F0" }}>{c}</strong>
        </span>
      ))}
      {graph.edges.length > 0 && (
        <span style={{ fontSize: 11, background: "#1E293B", color: "#94A3B8", borderRadius: 20, padding: "3px 10px" }}>
          🔗 Edges <strong style={{ color: "#E2E8F0" }}>{graph.edges.length}</strong>
        </span>
      )}
    </div>
  );
}

function OntologyPanel({ onDone }) {
  const [state, setState] = useState("idle"); // idle | running | done | error
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  async function run() {
    setState("running"); setResult(null); setErr(null);
    try {
      const r = await extractOntology();
      setResult(r); setState("done");
      setTimeout(onDone, 800); // auto-refresh graph
    } catch (e) { setErr(e.message); setState("error"); }
  }

  const RELATIONS = [
    { r: "READS_FROM", color: "#8B5CF6", desc: "SQL tables queried" },
    { r: "WRITES_TO",  color: "#EF4444", desc: "SQL tables inserted/updated" },
    { r: "DEPENDS_ON", color: "#F59E0B", desc: "Python/JS imports" },
    { r: "DERIVED_FROM", color: "#EC4899", desc: "Same-named table across repos" },
    { r: "DOCUMENTS",  color: "#10B981", desc: "CI/docs files referencing repo" },
  ];

  return (
    <div style={{ background: "#1E293B", border: "1px solid #334155", borderRadius: 12, padding: "18px 22px", marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: "#E2E8F0", marginBottom: 4 }}>
            🧠 Build Ontology  <span style={{ fontSize: 11, fontWeight: 400, color: "#64748B" }}>— cross-source relationship extraction</span>
          </div>
          <div style={{ fontSize: 12, color: "#94A3B8", marginBottom: 10, lineHeight: 1.6 }}>
            Fetches file contents from all normalized sources and runs:<br />
            <strong style={{ color: "#7DD3FC" }}>SQL analysis</strong> (sqlglot) → READS_FROM / WRITES_TO &nbsp;·&nbsp;
            <strong style={{ color: "#7DD3FC" }}>Python imports</strong> → DEPENDS_ON &nbsp;·&nbsp;
            <strong style={{ color: "#7DD3FC" }}>Name matching</strong> → DERIVED_FROM, DOCUMENTS
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 10 }}>
            {RELATIONS.map(({ r, color, desc }) => (
              <span key={r} style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11, background: "#0F172A", borderRadius: 20, padding: "3px 10px" }}>
                <span style={{ width: 20, height: 2, background: color, borderRadius: 1, display: "inline-block" }} />
                <span style={{ color: "#94A3B8", fontFamily: "monospace" }}>{r}</span>
                <span style={{ color: "#475569" }}>— {desc}</span>
              </span>
            ))}
          </div>
          {result && (
            <div style={{ background: "#0F172A", borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "#7DD3FC" }}>
              ✅ {result.message}
              {Object.keys(result.relations).length > 0 && (
                <div style={{ marginTop: 6, display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {Object.entries(result.relations).map(([r, c]) => (
                    <span key={r} style={{ background: "#1E293B", borderRadius: 10, padding: "1px 8px", fontFamily: "monospace", color: "#94A3B8" }}>{r}: {c}</span>
                  ))}
                </div>
              )}
            </div>
          )}
          {err && <div style={{ color: "#F87171", fontSize: 12, marginTop: 6 }}>{err}</div>}
        </div>
        <button type="button" onClick={run} disabled={state === "running"}
          style={{ background: state === "running" ? "#334155" : state === "done" ? "#059669" : "#7C3AED", color: "#fff", border: "none", borderRadius: 9, padding: "10px 20px", fontWeight: 700, fontSize: 14, cursor: state === "running" ? "not-allowed" : "pointer", whiteSpace: "nowrap", flexShrink: 0 }}>
          {state === "running" ? "⏳ Extracting…" : state === "done" ? "✅ Done" : "🧠 Extract ontology"}
        </button>
      </div>
    </div>
  );
}

export function GraphScreen({ onAddSource }) {
  const [graphState, setGraphState] = useState("loading");
  const [fullGraph, setFullGraph] = useState({ nodes: [], edges: [] });
  const [filteredGraph, setFilteredGraph] = useState({ nodes: [], edges: [] });
  const [sources, setSources] = useState([]);
  const [activeSourceIds, setActiveSourceIds] = useState(new Set());
  const [refreshKey, setRefreshKey] = useState(0);
  const [showOntologyPanel, setShowOntologyPanel] = useState(false);

  // Load sources
  useEffect(() => {
    listSources().then((rows) => {
      setSources(rows);
      setActiveSourceIds(new Set(rows.map((r) => r.id)));
    }).catch(() => {});
  }, []);

  // Load full graph
  useEffect(() => {
    let cancelled = false;
    setGraphState("loading");
    getGraph()
      .then((data) => {
        if (cancelled) return;
        setFullGraph(data);
        setFilteredGraph(data);
        setGraphState(data.nodes.length === 0 ? "empty" : "success");
      })
      .catch(() => { if (!cancelled) setGraphState("error"); });
    return () => { cancelled = true; };
  }, [refreshKey]);

  // Filter graph when activeSourceIds changes
  useEffect(() => {
    if (activeSourceIds.size === 0) {
      setFilteredGraph({ nodes: [], edges: [] });
      return;
    }
    const nodes = fullGraph.nodes.filter((n) => activeSourceIds.has(n.source_id));
    const nodeIds = new Set(nodes.map((n) => n.id));
    const edges = fullGraph.edges.filter(
      (e) => nodeIds.has(e.src_entity_id) && nodeIds.has(e.dst_entity_id)
    );
    setFilteredGraph({ nodes, edges });
  }, [activeSourceIds, fullGraph]);

  const handleToggleSource = useCallback((id) => {
    setActiveSourceIds((prev) => {
      const n = new Set(prev);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  }, []);

  const handleToggleAll = useCallback(() => {
    setActiveSourceIds((prev) => {
      if (sources.every((s) => prev.has(s.id))) return new Set();
      return new Set(sources.map((s) => s.id));
    });
  }, [sources]);

  // Adapt graph for GraphCanvas (rename fields)
  const canvasNodes = filteredGraph.nodes.map((n) => ({
    id: n.id, label: n.name, type: n.type, source_id: n.source_id,
  }));
  const canvasEdges = filteredGraph.edges.map((e) => ({
    id: e.id, source: e.src_entity_id, target: e.dst_entity_id, relation: e.relation,
  }));

  if (graphState === "loading") {
    return (
      <div style={{ display: "flex", gap: 16 }}>
        <div style={{ width: 240, height: 500, background: "#1E293B", borderRadius: 12, opacity: 0.5 }} />
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#64748B" }}>Loading graph…</div>
      </div>
    );
  }

  if (graphState === "error") {
    return <ErrorBanner message="Could not load the knowledge graph." />;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 56px - 48px)" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, flexShrink: 0 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>🕸️ Knowledge Graph</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13, margin: "2px 0 0" }}>
            {filteredGraph.nodes.length} entities · {filteredGraph.edges.length} edges
            {activeSourceIds.size < sources.length && ` (filtered: ${activeSourceIds.size}/${sources.length} sources)`}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" onClick={() => setRefreshKey((k) => k + 1)}
            style={{ background: "var(--bg-canvas)", color: "var(--text-primary)", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "7px 14px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
            ↺ Refresh
          </button>
          <button type="button" onClick={() => setShowOntologyPanel((v) => !v)}
            style={{ background: showOntologyPanel ? "#7C3AED" : "#2d1f5e", color: showOntologyPanel ? "#fff" : "#A78BFA", border: "1px solid #7C3AED44", borderRadius: 8, padding: "7px 14px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>
            🧠 Build Ontology
          </button>
          <button type="button" onClick={onAddSource}
            style={{ background: "#2563EB", color: "#fff", border: "none", borderRadius: 8, padding: "7px 16px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
            + Add source
          </button>
        </div>
      </div>

      {graphState === "empty" && fullGraph.nodes.length === 0 ? (
        <EmptyState
          message="No knowledge graph yet. Harvest a source and click 'Update Knowledge Graph' to populate the graph."
          actionLabel="Add a source"
          onAction={onAddSource}
        />
      ) : (
        <>
          {showOntologyPanel && (
            <OntologyPanel onDone={() => { setRefreshKey((k) => k + 1); setShowOntologyPanel(false); }} />
          )}
          {filteredGraph.nodes.length > 0 && <GraphStats graph={filteredGraph} />}
          <div style={{ display: "flex", gap: 12, flex: 1, minHeight: 0 }}>
            <SourceFilterPanel
              sources={sources}
              activeIds={activeSourceIds}
              onToggle={handleToggleSource}
              onToggleAll={handleToggleAll}
              graph={fullGraph}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              {filteredGraph.nodes.length === 0 ? (
                <div style={{ height: "100%", background: "#0D1117", borderRadius: 12, border: "1px solid #1E293B", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 12 }}>
                  <span style={{ fontSize: 40 }}>🔍</span>
                  <div style={{ fontSize: 14, color: "#64748B" }}>No sources selected — toggle sources in the panel to show entities</div>
                </div>
              ) : (
                <GraphCanvas nodes={canvasNodes} edges={canvasEdges} />
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
