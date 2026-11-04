import { useState } from "react";
import { useProject } from "../ProjectContext.jsx";
import { useIsDark } from "../useIsDark.js";
import { MCP_TOOLS } from "./MCPScreen.jsx";

function StatusBadge({ status }) {
  const color = status === "ok" ? "#059669" : status === "error" ? "#DC2626" : "#6B7280";
  const label = status === "ok" ? "Connected" : status === "error" ? "Failed" : "Untested";
  return (
    <span style={{ fontSize: 10, fontWeight: 700, color, background: `${color}22`, borderRadius: 20, padding: "2px 8px" }}>{label}</span>
  );
}

function ExternalServerRow({ url, onRemove, isDark }) {
  const [status, setStatus] = useState("idle");
  const [tools, setTools] = useState([]);

  async function test() {
    setStatus("testing");
    try {
      const r = await fetch(`${url.replace(/\/$/, "")}/tools`, { signal: AbortSignal.timeout(5000) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      const list = Array.isArray(data) ? data : (data.tools ?? []);
      setTools(list.map(t => t.name ?? t).filter(Boolean));
      setStatus("ok");
    } catch {
      setStatus("error");
      setTools([]);
    }
  }

  return (
    <div style={{ background: "var(--bg-canvas)", border: "1px solid var(--border-subtle)", borderRadius: 10, padding: "12px 14px", marginBottom: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontFamily: "monospace", color: isDark ? "#60A5FA" : "#2563EB", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", fontWeight: 600 }}>{url}</div>
        </div>
        <StatusBadge status={status} />
        <button type="button" onClick={test} disabled={status === "testing"}
          style={{ fontSize: 11, fontWeight: 600, background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 6, padding: "4px 10px", color: "var(--text-secondary)", cursor: status === "testing" ? "not-allowed" : "pointer" }}>
          {status === "testing" ? "Testing…" : "Test"}
        </button>
        <button type="button" onClick={onRemove}
          style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", fontSize: 16, lineHeight: 1, padding: "2px 4px" }}>✕</button>
      </div>
      {tools.length > 0 && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
          {tools.map(t => (
            <span key={t} style={{ fontSize: 10, fontFamily: "monospace", background: isDark ? "#1e3a5f" : "#EFF6FF", color: isDark ? "#60A5FA" : "#2563EB", borderRadius: 10, padding: "2px 8px" }}>{t}</span>
          ))}
        </div>
      )}
    </div>
  );
}

export function MCPSettingsScreen() {
  const isDark = useIsDark();
  const { mcpServers, addMcpServer, removeMcpServer } = useProject();
  const [newUrl, setNewUrl] = useState("");

  function handleAdd() {
    const url = newUrl.trim();
    if (!url) return;
    addMcpServer(url);
    setNewUrl("");
  }

  return (
    <div style={{ maxWidth: 820 }}>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", margin: "0 0 6px" }}>MCP Tools & Chat</h2>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>
          Configure built-in and external MCP tools available to all agents and chats. External servers are persisted globally across sessions.
        </p>
      </div>

      {/* Built-in tools */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 12 }}>
          Built-in tools
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 10 }}>
          {MCP_TOOLS.map(t => (
            <div key={t.name} style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 10, padding: "12px 14px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                <span style={{ fontSize: 18 }}>{t.icon}</span>
                <span style={{ fontSize: 12, fontFamily: "monospace", fontWeight: 700, color: isDark ? "#60A5FA" : "#2563EB" }}>{t.name}</span>
                <span style={{ marginLeft: "auto", fontSize: 10, background: "#05966922", color: "#059669", borderRadius: 20, padding: "2px 8px", fontWeight: 700 }}>active</span>
              </div>
              <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>{t.description}</div>
              <div style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 4, fontFamily: "monospace", opacity: 0.7 }}>{t.category}</div>
            </div>
          ))}
        </div>
      </div>

      {/* External MCP servers */}
      <div>
        <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 4 }}>
          External MCP servers
        </div>
        <p style={{ fontSize: 12, color: "var(--text-secondary)", margin: "0 0 14px" }}>
          Add any HTTP MCP server. Tools are fetched from <code style={{ fontFamily: "monospace", background: "var(--bg-canvas)", padding: "1px 5px", borderRadius: 4 }}>{"{url}/tools"}</code> and called at <code style={{ fontFamily: "monospace", background: "var(--bg-canvas)", padding: "1px 5px", borderRadius: 4 }}>{"{url}/tools/{name}"}</code>.
        </p>

        {mcpServers.length === 0 && (
          <div style={{ textAlign: "center", padding: "28px 0", color: "var(--text-secondary)", fontSize: 13, background: "var(--bg-canvas)", borderRadius: 10, border: "1px dashed var(--border-subtle)", marginBottom: 12 }}>
            No external servers configured yet
          </div>
        )}

        {mcpServers.map((url) => (
          <ExternalServerRow key={url} url={url} onRemove={() => removeMcpServer(url)} isDark={isDark} />
        ))}

        {/* Add new server */}
        <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
          <input
            value={newUrl}
            onChange={e => setNewUrl(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter") handleAdd(); }}
            placeholder="http://my-mcp-server:8080"
            style={{ flex: 1, border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "10px 14px", fontSize: 13, outline: "none", fontFamily: "monospace" }}
          />
          <button type="button" onClick={handleAdd} disabled={!newUrl.trim()}
            style={{ background: newUrl.trim() ? "#2563EB" : "var(--bg-canvas)", color: newUrl.trim() ? "#fff" : "var(--text-secondary)", border: "none", borderRadius: 8, padding: "10px 20px", fontWeight: 700, fontSize: 13, cursor: newUrl.trim() ? "pointer" : "not-allowed" }}>
            + Add server
          </button>
        </div>

        <div style={{ marginTop: 20, padding: "14px 16px", background: isDark ? "#1a1500" : "#FFFBEB", border: `1px solid ${isDark ? "#713f12" : "#FDE68A"}`, borderRadius: 10, fontSize: 12, color: isDark ? "#F59E0B" : "#92400E", lineHeight: 1.6 }}>
          <strong>Note:</strong> External MCP servers must expose a standard REST interface. Tools are discovered automatically and become available to all agents in this session. Servers added here persist across browser sessions.
        </div>
      </div>
    </div>
  );
}
