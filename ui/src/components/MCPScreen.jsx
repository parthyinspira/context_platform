import { useEffect, useState } from "react";

const MCP_SERVER_URL = import.meta.env.VITE_MCP_SERVER_URL ?? "http://localhost:8003";
const API_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// Tools defined on the MCP server — kept in sync with mcp/server.py
const MCP_TOOLS = [
  {
    name: "search_context",
    icon: "🔍",
    category: "Retrieval",
    description: "Full-text + semantic search over all harvested and indexed content. Returns chunks with source link, harvested_at and sensitivity.",
    params: [
      { name: "query", type: "string", required: true, description: "Natural-language search query" },
      { name: "limit", type: "integer", required: false, description: "Max results to return (default 5)" },
    ],
    returns: "Array of { text, source_link, harvested_at, sensitivity }",
    example: '{ "query": "how does claim data flow to Snowflake", "limit": 3 }',
  },
  {
    name: "get_entity",
    icon: "🏷️",
    category: "Graph",
    description: "Retrieve a single entity node (Repository, Service, Table, Person, …) by its UUID, including all properties and ontology metadata.",
    params: [
      { name: "entity_id", type: "string", required: true, description: "UUID of the entity" },
    ],
    returns: "Entity object with id, type, name, props, source_id, ontology_version",
    example: '{ "entity_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6" }',
  },
  {
    name: "get_graph",
    icon: "🕸️",
    category: "Graph",
    description: "Return graph nodes and edges, optionally filtered by entity type or source. Useful for understanding relationships across the knowledge graph.",
    params: [
      { name: "entity_type", type: "string", required: false, description: "Filter to one entity type (e.g. Table, Service)" },
      { name: "source_id", type: "string", required: false, description: "Filter to entities from one source" },
      { name: "limit", type: "integer", required: false, description: "Max nodes (default 50)" },
    ],
    returns: "{ nodes: [...], edges: [...] }",
    example: '{ "entity_type": "Table", "limit": 20 }',
  },
  {
    name: "get_lineage",
    icon: "🔗",
    category: "Graph",
    description: "Trace upstream and downstream data lineage for any entity. Follows READS_FROM, WRITES_TO and DERIVED_FROM edges to build the full lineage tree.",
    params: [
      { name: "entity_id", type: "string", required: true, description: "Starting entity UUID" },
      { name: "direction", type: "string", required: false, description: '"upstream" | "downstream" | "both" (default both)' },
      { name: "max_depth", type: "integer", required: false, description: "Max hops to traverse (default 5)" },
    ],
    returns: "{ nodes: [...], edges: [...], root_id }",
    example: '{ "entity_id": "...", "direction": "downstream", "max_depth": 3 }',
  },
  {
    name: "list_sources",
    icon: "⎇",
    category: "Registry",
    description: "List all registered sources with their type, URI, schedule, owner, sensitivity and last harvest timestamp.",
    params: [],
    returns: "Array of source objects",
    example: "{}",
  },
];

const CATEGORIES = [...new Set(MCP_TOOLS.map((t) => t.category))];

function StatusDot({ ok }) {
  return (
    <span style={{ width: 10, height: 10, borderRadius: "50%", display: "inline-block", background: ok ? "#059669" : "#DC2626", marginRight: 6, boxShadow: ok ? "0 0 0 3px #D1FAE5" : "0 0 0 3px #FEE2E2" }} />
  );
}

function ToolCard({ tool, expanded, onToggle }) {
  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 12, overflow: "hidden", marginBottom: 12 }}>
      <div onClick={onToggle} style={{ display: "flex", alignItems: "center", gap: 12, padding: "14px 20px", cursor: "pointer", userSelect: "none" }}>
        <span style={{ fontSize: 22 }}>{tool.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: "var(--text-primary)", fontFamily: "monospace" }}>{tool.name}</div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>{tool.description.split(".")[0]}.</div>
        </div>
        <span style={{ background: "#1e3a5f", color: "#60A5FA", borderRadius: 20, padding: "3px 10px", fontSize: 11, fontWeight: 600 }}>
          {tool.category}
        </span>
        <span style={{ fontSize: 16, color: "var(--text-secondary)", marginLeft: 4 }}>{expanded ? "▲" : "▼"}</span>
      </div>

      {expanded && (
        <div style={{ borderTop: "1px solid var(--border-subtle)", padding: "16px 20px", background: "var(--bg-canvas)" }}>
          <p style={{ fontSize: 13, color: "var(--text-primary)", marginTop: 0 }}>{tool.description}</p>

          {tool.params.length > 0 && (
            <>
              <div style={{ fontWeight: 600, fontSize: 12, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>Parameters</div>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, marginBottom: 14 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    {["Name", "Type", "Required", "Description"].map((h) => (
                      <th key={h} style={{ textAlign: "left", padding: "4px 8px", color: "var(--text-secondary)", fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tool.params.map((p) => (
                    <tr key={p.name} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                      <td style={{ padding: "5px 8px", fontFamily: "monospace", color: "#60A5FA" }}>{p.name}</td>
                      <td style={{ padding: "5px 8px", fontFamily: "monospace", color: "#A78BFA" }}>{p.type}</td>
                      <td style={{ padding: "5px 8px" }}>{p.required ? <span style={{ color: "var(--danger)", fontWeight: 700 }}>yes</span> : <span style={{ color: "var(--text-secondary)" }}>no</span>}</td>
                      <td style={{ padding: "5px 8px", color: "var(--text-primary)" }}>{p.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ fontWeight: 600, fontSize: 12, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 6 }}>Returns</div>
              <code style={{ fontSize: 12, color: "var(--text-primary)", background: "var(--bg-surface)", padding: "4px 8px", borderRadius: 6, display: "block", border: "1px solid var(--border-subtle)" }}>{tool.returns}</code>
            </div>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ fontWeight: 600, fontSize: 12, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 6 }}>Example input</div>
              <code style={{ fontSize: 11, color: "var(--success)", background: "#052e16", padding: "4px 8px", borderRadius: 6, display: "block", whiteSpace: "pre-wrap", border: "1px solid #05966933" }}>{tool.example}</code>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function MCPScreen() {
  const [apiOk, setApiOk] = useState(null);
  const [mcpOk, setMcpOk] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [catFilter, setCatFilter] = useState("All");

  useEffect(() => {
    fetch(`${API_URL}/health`).then((r) => setApiOk(r.ok)).catch(() => setApiOk(false));
    fetch(`${MCP_SERVER_URL}/health`).then((r) => setMcpOk(r.ok)).catch(() => setMcpOk(false));
  }, []);

  const filtered = catFilter === "All" ? MCP_TOOLS : MCP_TOOLS.filter((t) => t.category === catFilter);

  return (
    <div style={{ maxWidth: 860 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>MCP Tools</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: "4px 0 0" }}>
          Model Context Protocol tools exposed by this platform. Agents use these to query the knowledge graph.
        </p>
      </div>

      {/* Server status */}
      <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 12, padding: "16px 20px", marginBottom: 24, display: "flex", gap: 32, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 6 }}>API Server</div>
          <div style={{ display: "flex", alignItems: "center", fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
            <StatusDot ok={apiOk} />
            {apiOk === null ? "Checking…" : apiOk ? "Online" : "Offline"}
            <span style={{ fontFamily: "monospace", fontSize: 12, color: "var(--text-secondary)", marginLeft: 8 }}>{API_URL}</span>
          </div>
        </div>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 6 }}>MCP Server</div>
          <div style={{ display: "flex", alignItems: "center", fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
            <StatusDot ok={mcpOk} />
            {mcpOk === null ? "Checking…" : mcpOk ? "Online" : "Offline"}
            <span style={{ fontFamily: "monospace", fontSize: 12, color: "var(--text-secondary)", marginLeft: 8 }}>{MCP_SERVER_URL}</span>
          </div>
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 6 }}>MCP Endpoint</div>
          <code style={{ fontSize: 12, color: "#60A5FA", background: "#1e3a5f", padding: "3px 8px", borderRadius: 6 }}>{MCP_SERVER_URL}/mcp</code>
        </div>
      </div>

      {/* Category filter */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        {["All", ...CATEGORIES].map((cat) => (
          <button key={cat} type="button" onClick={() => setCatFilter(cat)}
            style={{ padding: "6px 14px", borderRadius: 20, border: "none", fontWeight: 600, fontSize: 13, cursor: "pointer", background: cat === catFilter ? "#2563EB" : "var(--bg-canvas)", color: cat === catFilter ? "#fff" : "var(--text-secondary)" }}>
            {cat}
          </button>
        ))}
        <span style={{ marginLeft: "auto", fontSize: 13, color: "var(--text-secondary)", alignSelf: "center" }}>{filtered.length} tool{filtered.length !== 1 ? "s" : ""}</span>
      </div>

      {/* Tool cards */}
      {filtered.map((tool) => (
        <ToolCard key={tool.name} tool={tool} expanded={expanded === tool.name} onToggle={() => setExpanded(expanded === tool.name ? null : tool.name)} />
      ))}

      {/* Connect instructions */}
      <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 12, padding: "20px 24px", marginTop: 8 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: "var(--text-primary)", marginBottom: 10 }}>Connect an external client</div>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 0 }}>Point any MCP-compatible client (Claude Desktop, Claude Code, Cursor, …) at the endpoint below:</p>
        <code style={{ display: "block", background: "#0D1117", color: "#7DD3FC", padding: "12px 16px", borderRadius: 8, fontSize: 13, marginBottom: 12, border: "1px solid var(--border-subtle)" }}>
          {`{
  "mcpServers": {
    "context-platform": {
      "url": "${MCP_SERVER_URL}/mcp",
      "transport": "streamable-http"
    }
  }
}`}
        </code>
        <p style={{ fontSize: 12, color: "var(--text-secondary)", margin: 0 }}>All {MCP_TOOLS.length} tools above become available automatically once connected.</p>
      </div>
    </div>
  );
}

export { MCP_TOOLS };
