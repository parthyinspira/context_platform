import { useEffect, useRef, useState } from "react";
import { agentChat } from "../api.js";
import { useIsDark } from "../useIsDark.js";
import { useProject } from "../ProjectContext.jsx";
import { MCP_TOOLS } from "./MCPScreen.jsx";

function ToolCallBubble({ call }) {
  const [open, setOpen] = useState(false);
  const isDark = useIsDark();
  return (
    <div style={{ marginBottom: 6 }}>
      <button type="button" onClick={() => setOpen((v) => !v)}
        style={{ display: "flex", alignItems: "center", gap: 7, background: isDark ? "#1e2a3a" : "#EFF6FF", border: `1px solid ${isDark ? "#334155" : "#BFDBFE"}`, borderRadius: 8, padding: "5px 12px", cursor: "pointer", fontSize: 11, color: isDark ? "#60A5FA" : "#2563EB", fontWeight: 600 }}>
        <span>🔌</span>
        <span style={{ fontFamily: "monospace" }}>{call.tool}</span>
        <span style={{ fontWeight: 400, color: isDark ? "#64748B" : "#6B7280" }}>({Object.keys(call.input).map(k => `${k}="${JSON.stringify(call.input[k]).slice(1,-1)}"`).join(", ")})</span>
        <span style={{ marginLeft: 4 }}>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <pre style={{ background: isDark ? "#0F172A" : "#F8FAFC", border: `1px solid ${isDark ? "#1E293B" : "#E2E8F0"}`, borderRadius: 8, padding: "10px 14px", fontSize: 11, color: isDark ? "#94A3B8" : "#475569", whiteSpace: "pre-wrap", wordBreak: "break-word", marginTop: 4, maxHeight: 200, overflow: "auto" }}>
          {(() => { try { return JSON.stringify(JSON.parse(call.result), null, 2); } catch { return call.result; } })()}
        </pre>
      )}
    </div>
  );
}

function Message({ msg, isDark }) {
  const isUser = msg.role === "user";
  const isError = msg.role === "error";

  if (isUser) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 14 }}>
        <div style={{ maxWidth: "72%", background: "#2563EB", color: "#fff", borderRadius: "14px 14px 4px 14px", padding: "10px 15px", fontSize: 13, lineHeight: 1.6 }}>
          {msg.content}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div style={{ marginBottom: 14, padding: "10px 14px", background: isDark ? "#2d1515" : "#FEF2F2", border: `1px solid ${isDark ? "#7f1d1d" : "#FECACA"}`, borderRadius: 10, fontSize: 13, color: isDark ? "#F87171" : "#DC2626" }}>
        ⚠️ {msg.content}
      </div>
    );
  }

  return (
    <div style={{ marginBottom: 18 }}>
      {msg.toolCalls?.length > 0 && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 6 }}>Tool calls</div>
          {msg.toolCalls.map((c, i) => <ToolCallBubble key={i} call={c} />)}
        </div>
      )}
      <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
        <div style={{ width: 28, height: 28, borderRadius: "50%", background: isDark ? "#1e2a3a" : "#EFF6FF", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, flexShrink: 0 }}>
          🤖
        </div>
        <div style={{ flex: 1, background: isDark ? "var(--bg-surface)" : "#F8FAFC", border: `1px solid var(--border-subtle)`, borderRadius: "4px 14px 14px 14px", padding: "10px 15px", fontSize: 13, lineHeight: 1.7, color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>
          {msg.content}
        </div>
      </div>
    </div>
  );
}

function McpServerRow({ url, onRemove }) {
  const isDark = useIsDark();
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", background: isDark ? "#1e2a3a" : "#EFF6FF", borderRadius: 8, marginBottom: 6 }}>
      <span style={{ fontSize: 12, fontFamily: "monospace", flex: 1, color: isDark ? "#60A5FA" : "#2563EB", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{url}</span>
      <button type="button" onClick={onRemove} style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", fontSize: 14, lineHeight: 1 }}>✕</button>
    </div>
  );
}

export function AgentChat({ agent }) {
  const isDark = useIsDark();
  const { mcpServers, addMcpServer, removeMcpServer } = useProject();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showToolPanel, setShowToolPanel] = useState(false);
  const [enabledTools, setEnabledTools] = useState(new Set(agent.tools ?? MCP_TOOLS.map(t => t.name)));
  const [sessionServers, setSessionServers] = useState(agent.extraMcpServers ?? []);
  const [newServerUrl, setNewServerUrl] = useState("");
  const bottomRef = useRef(null);

  // Merged deduplicated list: global (persisted) + session-only
  const allExtraServers = [...new Set([...mcpServers, ...sessionServers])];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Reset on agent change
  useEffect(() => {
    setMessages([]);
    setEnabledTools(new Set(agent.tools ?? MCP_TOOLS.map(t => t.name)));
    setSessionServers(agent.extraMcpServers ?? []);
  }, [agent.id ?? agent.label]);

  function toggleTool(name) {
    setEnabledTools(s => { const n = new Set(s); n.has(name) ? n.delete(name) : n.add(name); return n; });
  }

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    const userMsg = { role: "user", content: text };
    const history = [...messages, userMsg];
    setMessages(history);
    setLoading(true);
    try {
      const payload = {
        messages: history.filter(m => m.role === "user" || m.role === "assistant").map(m => ({ role: m.role, content: m.content })),
        system_prompt: agent.systemPrompt ?? agent.description ?? "You are a helpful assistant. Use the available tools and cite your sources.",
        model: agent.model ?? "claude-sonnet-4-5",
        enabled_tools: [...enabledTools],
        extra_tool_servers: allExtraServers,
      };
      const resp = await agentChat(payload);
      setMessages(prev => [...prev, { role: "assistant", content: resp.answer, toolCalls: resp.tool_calls }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "error", content: e.message }]);
    }
    setLoading(false);
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 160px)", minHeight: 400 }}>
      {/* Header bar */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 18px", background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "12px 12px 0 0" }}>
        <span style={{ fontSize: 20 }}>{agent.icon ?? "🤖"}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: "var(--text-primary)" }}>{agent.label ?? agent.name}</div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>{agent.model ?? "claude-sonnet-4-5"} · {enabledTools.size} tools active</div>
        </div>
        <button type="button" onClick={() => setShowToolPanel(v => !v)}
          style={{ background: showToolPanel ? "#7C3AED" : "var(--bg-canvas)", border: `1px solid ${showToolPanel ? "#7C3AED" : "var(--border-subtle)"}`, color: showToolPanel ? "#fff" : "var(--text-secondary)", borderRadius: 8, padding: "5px 12px", fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
          🔌 Tools & MCP
        </button>
        {messages.length > 0 && (
          <button type="button" onClick={() => setMessages([])}
            style={{ background: "var(--bg-canvas)", border: "1px solid var(--border-subtle)", color: "var(--text-secondary)", borderRadius: 8, padding: "5px 12px", fontSize: 12, cursor: "pointer" }}>
            🗑 Clear
          </button>
        )}
      </div>

      <div style={{ display: "flex", flex: 1, minHeight: 0, border: "1px solid var(--border-subtle)", borderTop: "none", borderRadius: "0 0 12px 12px", overflow: "hidden" }}>
        {/* Chat area */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: "20px 20px 10px", background: isDark ? "#0A0D12" : "#FAFBFC" }}>
            {messages.length === 0 && (
              <div style={{ textAlign: "center", color: "var(--text-secondary)", marginTop: 60 }}>
                <div style={{ fontSize: 36, marginBottom: 10 }}>💬</div>
                <div style={{ fontWeight: 600, fontSize: 15 }}>Ask anything about your knowledge graph</div>
                <div style={{ fontSize: 12, marginTop: 6 }}>The agent will search your sources and cite its findings</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", marginTop: 20 }}>
                  {["What entities are in the graph?", "Show me SQL tables and their relations", "What does this codebase do?"].map(q => (
                    <button key={q} type="button" onClick={() => { setInput(q); }}
                      style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 20, padding: "6px 14px", fontSize: 12, color: "var(--text-primary)", cursor: "pointer" }}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => <Message key={i} msg={m} isDark={isDark} />)}
            {loading && (
              <div style={{ display: "flex", gap: 10, alignItems: "flex-start", marginBottom: 14 }}>
                <div style={{ width: 28, height: 28, borderRadius: "50%", background: isDark ? "#1e2a3a" : "#EFF6FF", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>🤖</div>
                <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "4px 14px 14px 14px", padding: "12px 16px" }}>
                  <div style={{ display: "flex", gap: 4 }}>
                    {[0,1,2].map(i => <span key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "#2563EB", display: "inline-block", animation: `pulse 1.2s ${i*0.2}s infinite` }} />)}
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border-subtle)", background: "var(--bg-surface)", display: "flex", gap: 10 }}>
            <textarea
              value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
              placeholder="Ask a question… (Enter to send, Shift+Enter for newline)"
              rows={2}
              style={{ flex: 1, border: "1px solid var(--border-subtle)", borderRadius: 10, padding: "10px 14px", fontSize: 13, resize: "none", outline: "none", fontFamily: "inherit", lineHeight: 1.5 }}
            />
            <button type="button" onClick={send} disabled={loading || !input.trim()}
              style={{ background: loading || !input.trim() ? "var(--bg-canvas)" : "#2563EB", color: loading || !input.trim() ? "var(--text-secondary)" : "#fff", border: "none", borderRadius: 10, padding: "0 20px", fontSize: 18, cursor: loading || !input.trim() ? "not-allowed" : "pointer", flexShrink: 0 }}>
              ➤
            </button>
          </div>
        </div>

        {/* Tools & MCP sidebar */}
        {showToolPanel && (
          <div style={{ width: 260, flexShrink: 0, borderLeft: "1px solid var(--border-subtle)", background: "var(--bg-surface)", overflowY: "auto", padding: "14px 14px" }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 10 }}>Built-in tools</div>
            {MCP_TOOLS.map(t => {
              const on = enabledTools.has(t.name);
              return (
                <div key={t.name} onClick={() => toggleTool(t.name)}
                  style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 10px", borderRadius: 8, border: `1px solid ${on ? "#2563EB" : "var(--border-subtle)"}`, background: on ? (isDark ? "#1e3a5f" : "#EFF6FF") : "var(--bg-canvas)", cursor: "pointer", marginBottom: 6 }}>
                  <span>{t.icon}</span>
                  <span style={{ flex: 1, fontSize: 11, fontFamily: "monospace", color: on ? (isDark ? "#60A5FA" : "#2563EB") : "var(--text-primary)", fontWeight: 600 }}>{t.name}</span>
                  <div style={{ width: 14, height: 14, borderRadius: "50%", border: `2px solid ${on ? "#2563EB" : "var(--border-subtle)"}`, background: on ? "#2563EB" : "transparent", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    {on && <span style={{ color: "#fff", fontSize: 9 }}>✓</span>}
                  </div>
                </div>
              );
            })}

            <div style={{ height: 1, background: "var(--border-subtle)", margin: "14px 0" }} />

            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 6 }}>Global MCP servers</div>
            {mcpServers.length === 0 && <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 6 }}>None — add in Settings → MCP & Chat</div>}
            {mcpServers.map((url) => (
              <McpServerRow key={url} url={url} onRemove={() => removeMcpServer(url)} />
            ))}

            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".08em", margin: "10px 0 6px" }}>Session servers</div>
            {sessionServers.map((url, i) => (
              <McpServerRow key={i} url={url} onRemove={() => setSessionServers(s => s.filter((_, j) => j !== i))} />
            ))}
            <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
              <input value={newServerUrl} onChange={e => setNewServerUrl(e.target.value)}
                placeholder="http://my-mcp:8080"
                onKeyDown={e => { if (e.key === "Enter" && newServerUrl.trim()) { setSessionServers(s => [...s, newServerUrl.trim()]); setNewServerUrl(""); }}}
                style={{ flex: 1, border: "1px solid var(--border-subtle)", borderRadius: 7, padding: "6px 10px", fontSize: 11, outline: "none" }} />
              <button type="button"
                onClick={() => { if (newServerUrl.trim()) { addMcpServer(newServerUrl.trim()); setNewServerUrl(""); }}}
                title="Add globally (persisted)"
                style={{ background: "#7C3AED", color: "#fff", border: "none", borderRadius: 7, padding: "6px 10px", fontSize: 11, cursor: "pointer", fontWeight: 700 }}>Global</button>
              <button type="button"
                onClick={() => { if (newServerUrl.trim()) { setSessionServers(s => [...s, newServerUrl.trim()]); setNewServerUrl(""); }}}
                title="Add for this session only"
                style={{ background: "#2563EB", color: "#fff", border: "none", borderRadius: 7, padding: "6px 10px", fontSize: 11, cursor: "pointer", fontWeight: 700 }}>Session</button>
            </div>
            <div style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 6, lineHeight: 1.5 }}>
              <strong>Global</strong>: saved across sessions. <strong>Session</strong>: this chat only.
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
          30% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
