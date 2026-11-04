import { useState } from "react";
import { useProject } from "../ProjectContext.jsx";
import { useIsDark } from "../useIsDark.js";
import { MCP_TOOLS } from "./MCPScreen.jsx";

// ── Demo agents (built-in) ────────────────────────────────────────────────────

const DEMO_AGENTS = [
  { id: "workflow",    icon: "🔀", label: "Workflow",     description: "Change-request impact analysis", tasks: [{ key: "rename-cust-id", label: "Rename column CUSTOMER.CUST_ID" }] },
  { id: "research",   icon: "🔬", label: "Research",     description: "How does customer data reach the revenue dashboard?", tasks: [{ key: "customer-to-revenue", label: "Customer data → Revenue Dashboard" }] },
  { id: "prod_support", icon: "🚨", label: "Prod Support", description: "Stale data triage", tasks: [{ key: "stale-revenue-dashboard", label: "Revenue dashboard shows stale data" }] },
  { id: "call_centre", icon: "📞", label: "Call Centre",  description: "Policy and product answers", tasks: [{ key: "mid-year-contribution", label: "Mid-year contribution change rule" }, { key: "out-of-scope", label: "Out-of-scope question (escalation demo)" }] },
];


const LLM_MODELS = [
  "claude-sonnet-4-5", "claude-haiku-4-5", "claude-opus-4-5",
  "gpt-4o", "gpt-4o-mini",
  "meta-llama/Llama-3.1-70B-Instruct",
  "gemini-1.5-pro",
];

const CAPABILITY_OPTIONS = [
  { id: "search",  icon: "🔍", label: "Context search",   description: "Search the knowledge graph by natural language" },
  { id: "graph",   icon: "🕸️", label: "Graph traversal",  description: "Traverse entity relationships and lineage" },
  { id: "lineage", icon: "🔗", label: "Data lineage",     description: "Trace upstream/downstream data flows" },
  { id: "sources", icon: "⎇",  label: "Source registry",  description: "List and inspect registered sources" },
  { id: "escalate",icon: "🚨", label: "Escalation",       description: "Escalate when no sufficient evidence is found" },
];

// ── Agent form ────────────────────────────────────────────────────────────────

const AGENT_ICONS = ["🤖", "🔬", "📊", "🔀", "📞", "🚨", "🏥", "💳", "🏦", "🛡️", "⚡", "🌐"];

function AgentForm({ initial, onSave, onCancel }) {
  const { activeProject, mcpServers } = useProject();
  const isDark = useIsDark();
  const projectModel = activeProject.settings?.llmModel ?? "claude-sonnet-4-5";

  const [name, setName] = useState(initial?.name ?? "");
  const [icon, setIcon] = useState(initial?.icon ?? "🤖");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [systemPrompt, setSystemPrompt] = useState(initial?.systemPrompt ?? "You are a helpful assistant with access to the project knowledge graph. Answer questions using the available tools and always cite your sources.");
  const [model, setModel] = useState(initial?.model ?? projectModel);
  const [tools, setTools] = useState(new Set(initial?.tools ?? MCP_TOOLS.map((t) => t.name)));
  const [capabilities, setCapabilities] = useState(new Set(initial?.capabilities ?? CAPABILITY_OPTIONS.map((c) => c.id)));

  function toggleTool(name) { setTools((s) => { const n = new Set(s); n.has(name) ? n.delete(name) : n.add(name); return n; }); }
  function toggleCap(id)   { setCapabilities((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; }); }

  function handleSave() {
    if (!name.trim()) return;
    onSave({
      id: initial?.id ?? crypto.randomUUID(),
      name: name.trim(), icon, description, systemPrompt,
      model, tools: [...tools], capabilities: [...capabilities],
      createdAt: initial?.createdAt ?? new Date().toISOString(),
    });
  }

  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 14, padding: "24px 28px" }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", margin: "0 0 20px" }}>
        {initial ? "Edit agent" : "Create new agent"}
      </h2>

      {/* Identity */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <div>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>Icon</label>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap", maxWidth: 220 }}>
            {AGENT_ICONS.map((ic) => (
              <button key={ic} type="button" onClick={() => setIcon(ic)}
                style={{ width: 34, height: 34, borderRadius: 8, border: `2px solid ${ic === icon ? "#2563EB" : "var(--border-subtle)"}`, background: "var(--bg-canvas)", fontSize: 18, cursor: "pointer" }}>
                {ic}
              </button>
            ))}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>Name <span style={{ color: "var(--danger)" }}>*</span></label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Claims Analyst"
            style={{ width: "100%", boxSizing: "border-box", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "9px 12px", fontSize: 14, outline: "none" }} />
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6, marginTop: 12 }}>Description</label>
          <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What does this agent do?"
            style={{ width: "100%", boxSizing: "border-box", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "9px 12px", fontSize: 13, outline: "none" }} />
        </div>
      </div>

      {/* System prompt */}
      <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>System prompt</label>
      <textarea value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} rows={4}
        style={{ width: "100%", boxSizing: "border-box", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "9px 12px", fontSize: 13, outline: "none", resize: "vertical", fontFamily: "inherit", marginBottom: 16 }} />

      {/* Model */}
      <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>LLM model</label>
      <select value={model} onChange={(e) => setModel(e.target.value)}
        style={{ width: "100%", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "9px 12px", fontSize: 13, outline: "none", marginBottom: 20 }}>
        {LLM_MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
      </select>

      {/* MCP Tools */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 10 }}>
          🔌 Built-in MCP Tools — {tools.size} of {MCP_TOOLS.length} enabled
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {MCP_TOOLS.map((tool) => {
            const on = tools.has(tool.name);
            return (
              <div key={tool.name} onClick={() => toggleTool(tool.name)}
                style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 10, border: `1.5px solid ${on ? "#2563EB" : "var(--border-subtle)"}`, background: on ? (isDark ? "#1e3a5f" : "#EFF6FF") : "var(--bg-canvas)", cursor: "pointer" }}>
                <span style={{ fontSize: 18 }}>{tool.icon}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: on ? (isDark ? "#60A5FA" : "#2563EB") : "var(--text-primary)", fontFamily: "monospace" }}>{tool.name}</div>
                  <div style={{ fontSize: 11, color: "var(--text-secondary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{tool.category}</div>
                </div>
                <div style={{ width: 18, height: 18, borderRadius: "50%", border: `2px solid ${on ? "#2563EB" : "var(--border-subtle)"}`, background: on ? "#2563EB" : "transparent", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  {on && <span style={{ color: "#fff", fontSize: 11 }}>✓</span>}
                </div>
              </div>
            );
          })}
        </div>

        {/* External MCP servers from Settings → MCP */}
        {mcpServers && mcpServers.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>
              External MCP Servers (from Settings → MCP)
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {mcpServers.map(url => (
                <div key={url} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border-subtle)", background: "var(--bg-canvas)" }}>
                  <span style={{ fontSize: 14 }}>🔌</span>
                  <span style={{ flex: 1, fontSize: 12, color: "var(--text-secondary)", fontFamily: "monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{url}</span>
                  <span style={{ fontSize: 10, fontWeight: 700, color: "#059669", background: "#05966922", borderRadius: 10, padding: "2px 8px" }}>Auto-included</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Capabilities */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 10 }}>
          ⚡ Capabilities
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {CAPABILITY_OPTIONS.map((cap) => {
            const on = capabilities.has(cap.id);
            return (
              <div key={cap.id} onClick={() => toggleCap(cap.id)}
                style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 10, border: `1.5px solid ${on ? "#059669" : "var(--border-subtle)"}`, background: on ? (isDark ? "#052e16" : "#F0FDF4") : "var(--bg-canvas)", cursor: "pointer" }}>
                <span style={{ fontSize: 18 }}>{cap.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: on ? (isDark ? "#34D399" : "#059669") : "var(--text-primary)" }}>{cap.label}</div>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{cap.description}</div>
                </div>
                <div style={{ width: 18, height: 18, borderRadius: 4, border: `2px solid ${on ? "#059669" : "var(--border-subtle)"}`, background: on ? "#059669" : "transparent", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {on && <span style={{ color: "#fff", fontSize: 11 }}>✓</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 10 }}>
        <button type="button" onClick={handleSave} disabled={!name.trim()}
          style={{ background: "#2563EB", color: "#fff", border: "none", borderRadius: 8, padding: "10px 24px", fontWeight: 700, fontSize: 14, cursor: name.trim() ? "pointer" : "not-allowed", opacity: name.trim() ? 1 : 0.5 }}>
          {initial ? "Save changes" : "✚ Create agent"}
        </button>
        <button type="button" onClick={onCancel}
          style={{ background: "transparent", color: "var(--text-secondary)", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "10px 20px", fontWeight: 600, fontSize: 14, cursor: "pointer" }}>
          Cancel
        </button>
      </div>
    </div>
  );
}

// ── Agent card ────────────────────────────────────────────────────────────────

function AgentCard({ agent, selected, onClick, onEdit, onDelete, onClone, isDemo }) {
  const isDark = useIsDark();
  return (
    <div onClick={onClick}
      style={{ background: "var(--bg-surface)", border: `2px solid ${selected ? "#2563EB" : "var(--border-subtle)"}`, borderRadius: 12, padding: "14px 16px", cursor: "pointer", position: "relative" }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
        <div style={{ width: 36, height: 36, borderRadius: 10, background: selected ? (isDark ? "#1e3a5f" : "#EFF6FF") : "var(--bg-canvas)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0 }}>
          {agent.icon ?? "🤖"}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: "var(--text-primary)" }}>{agent.label ?? agent.name}</div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>{agent.description}</div>
          <div style={{ display: "flex", gap: 4, marginTop: 6, flexWrap: "wrap" }}>
            {(agent.tools ?? MCP_TOOLS.map((t) => t.name)).slice(0, 3).map((t) => (
              <span key={t} style={{ fontSize: 10, background: isDark ? "#1e3a5f" : "#EFF6FF", color: isDark ? "#60A5FA" : "#2563EB", borderRadius: 10, padding: "1px 7px", fontFamily: "monospace" }}>{t}</span>
            ))}
            {(agent.tools ?? []).length > 3 && <span style={{ fontSize: 10, color: "var(--text-secondary)" }}>+{agent.tools.length - 3}</span>}
          </div>
        </div>
        {isDemo && <span style={{ fontSize: 10, background: "var(--bg-canvas)", color: "var(--text-secondary)", borderRadius: 10, padding: "2px 8px", fontWeight: 600, flexShrink: 0 }}>demo</span>}
      </div>
      <div style={{ display: "flex", gap: 6, marginTop: 10, justifyContent: "flex-end" }}>
        {isDemo ? (
          <button type="button" onClick={(e) => { e.stopPropagation(); onClone(); }}
            style={{ fontSize: 11, background: isDark ? "#1e3a5f" : "#EFF6FF", border: "none", borderRadius: 6, padding: "4px 10px", color: isDark ? "#60A5FA" : "#2563EB", cursor: "pointer", fontWeight: 600 }}>
            ✏️ Clone & Edit
          </button>
        ) : (
          <>
            <button type="button" onClick={(e) => { e.stopPropagation(); onEdit(); }}
              style={{ fontSize: 11, background: "var(--bg-canvas)", border: "none", borderRadius: 6, padding: "4px 10px", color: "var(--text-primary)", cursor: "pointer", fontWeight: 600 }}>✏️ Edit</button>
            <button type="button" onClick={(e) => { e.stopPropagation(); onDelete(); }}
              style={{ fontSize: 11, background: isDark ? "#2d1515" : "#FEF2F2", border: "none", borderRadius: 6, padding: "4px 10px", color: "var(--danger)", cursor: "pointer", fontWeight: 600 }}>🗑</button>
          </>
        )}
      </div>
    </div>
  );
}

// ── Main screen ───────────────────────────────────────────────────────────────

export function AgentsScreen() {
  const { activeProject, saveAgent, deleteAgent } = useProject();
  const customAgents = activeProject.agents ?? [];

  const [mode, setMode] = useState("list"); // list | create | edit
  const [editingAgent, setEditingAgent] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const selectedDemo = DEMO_AGENTS.find((a) => a.id === selectedId);

  function handleSave(agent) {
    saveAgent(activeProject.id, agent);
    setMode("list");
    setEditingAgent(null);
  }

  if (mode === "create" || mode === "edit") {
    return (
      <div style={{ maxWidth: 820 }}>
        <AgentForm initial={editingAgent} onSave={handleSave} onCancel={() => { setMode("list"); setEditingAgent(null); }} />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", gap: 24, maxWidth: 1100 }}>
      {/* Left — agent library */}
      <div style={{ width: 280, flexShrink: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Agents</h2>
          <button type="button" onClick={() => { setMode("create"); setEditingAgent(null); }}
            style={{ background: "#2563EB", color: "#fff", border: "none", borderRadius: 7, padding: "6px 12px", fontWeight: 700, fontSize: 12, cursor: "pointer" }}>
            + New
          </button>
        </div>

        {/* Custom agents */}
        {customAgents.length > 0 && (
          <>
            <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 8 }}>
              {activeProject.icon} {activeProject.name}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
              {customAgents.map((a) => (
                <AgentCard key={a.id} agent={a} selected={selectedId === a.id}
                  onClick={() => setSelectedId(a.id)}
                  onEdit={() => { setEditingAgent(a); setMode("edit"); }}
                  onDelete={() => { deleteAgent(activeProject.id, a.id); if (selectedId === a.id) setSelectedId(null); }} />
              ))}
            </div>
          </>
        )}

        {/* Demo agents */}
        <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 8 }}>Demo agents</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {DEMO_AGENTS.map((a) => (
            <AgentCard key={a.id} agent={a} isDemo selected={selectedId === a.id}
              onClick={() => setSelectedId(a.id)}
              onClone={() => {
                setEditingAgent({
                  name: a.label,
                  icon: a.icon ?? "🤖",
                  description: a.description,
                  systemPrompt: `You are a ${a.label} agent. ${a.description}. Use the available MCP tools to answer questions grounded in the knowledge graph. Always cite your sources.`,
                  model: "claude-sonnet-4-5",
                  tools: MCP_TOOLS.map((t) => t.name),
                  capabilities: ["search", "graph", "lineage", "sources", "escalate"],
                });
                setMode("create");
              }} />
          ))}
        </div>
      </div>

      {/* Right — agent detail panel */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {!selectedId ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 300, color: "var(--text-secondary)", gap: 10 }}>
            <span style={{ fontSize: 48 }}>🤖</span>
            <div style={{ fontSize: 15, fontWeight: 600 }}>Select an agent to view</div>
            <div style={{ fontSize: 13 }}>Or create a custom agent with + New</div>
          </div>
        ) : (() => {
          const agent = selectedDemo
            ? { ...selectedDemo, name: selectedDemo.label, tools: MCP_TOOLS.map(t => t.name) }
            : customAgents.find((x) => x.id === selectedId);
          if (!agent) return null;
          return (
            <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 12, padding: "24px 28px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 20 }}>
                <div style={{ width: 48, height: 48, borderRadius: 12, background: "#1e3a5f", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24 }}>{agent.icon ?? "🤖"}</div>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>{agent.name ?? agent.label}</div>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 2 }}>{agent.description}</div>
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 6 }}>System Prompt</div>
                  <div style={{ background: "var(--bg-canvas)", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "var(--text-primary)", lineHeight: 1.6, whiteSpace: "pre-wrap", maxHeight: 160, overflowY: "auto" }}>
                    {agent.systemPrompt ?? `You are a ${agent.name ?? agent.label} agent. ${agent.description}`}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 6 }}>Tools</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {(agent.tools ?? []).map(t => (
                      <span key={t} style={{ background: "#1e3a5f", color: "#60A5FA", borderRadius: 20, padding: "3px 10px", fontSize: 11, fontWeight: 600, fontFamily: "monospace" }}>{t}</span>
                    ))}
                  </div>
                </div>
                {agent.model && (
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 4 }}>Model</div>
                    <span style={{ fontSize: 13, color: "var(--text-primary)", fontFamily: "monospace" }}>{agent.model}</span>
                  </div>
                )}
                <div style={{ paddingTop: 8, borderTop: "1px solid var(--border-subtle)", display: "flex", gap: 10 }}>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>To chat with this agent, go to the <strong style={{ color: "var(--text-primary)" }}>Chat</strong> tab and select Agent mode.</div>
                </div>
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
