import { useState, useRef, useEffect } from "react";
import { agentChat } from "../api.js";
import { useProject } from "../ProjectContext.jsx";

const DEMO_AGENTS = [
  { id: "workflow",     icon: "🔀", name: "Workflow",     description: "Change-request impact analysis", systemPrompt: "You are a workflow impact analysis agent. Analyse change requests and assess their downstream impact using the knowledge graph.", tools: ["search_context","get_graph","get_entity","list_sources"] },
  { id: "research",    icon: "🔬", name: "Research",     description: "Deep research across sources", systemPrompt: "You are a research agent. Answer complex questions by searching the knowledge graph and synthesising information from multiple sources.", tools: ["search_context","get_graph","get_entity","list_sources"] },
  { id: "prod_support",icon: "🚨", name: "Prod Support", description: "Stale data triage", systemPrompt: "You are a production support agent. Diagnose data freshness and pipeline issues by querying the knowledge graph.", tools: ["search_context","get_graph","get_entity","list_sources"] },
  { id: "call_centre", icon: "📞", name: "Call Centre",  description: "Policy and product answers", systemPrompt: "You are a call-centre support agent. Answer policy and product questions using the knowledge graph. Escalate when you lack sufficient evidence.", tools: ["search_context","list_sources"] },
];



function MsgBubble({ msg }) {
  const isUser = msg.role === "user";
  const isError = msg.role === "error";

  if (isError) {
    return (
      <div style={{ padding: "10px 14px", background: "#2D1515", border: "1px solid #7F1D1D", borderRadius: 10, color: "#FCA5A5", fontSize: 13, margin: "4px 0" }}>
        {msg.content}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", margin: "6px 0" }}>
      {!isUser && (
        <div style={{ width: 28, height: 28, borderRadius: "50%", background: "#2563EB", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, flexShrink: 0, marginRight: 8, marginTop: 2 }}>🧠</div>
      )}
      <div style={{
        maxWidth: "72%",
        padding: "10px 14px",
        borderRadius: isUser ? "16px 16px 4px 16px" : "4px 16px 16px 16px",
        background: isUser ? "#2563EB" : "var(--bg-surface)",
        color: isUser ? "#fff" : "var(--text-primary)",
        fontSize: 14,
        lineHeight: 1.6,
        border: isUser ? "none" : "1px solid var(--border-subtle)",
        whiteSpace: "pre-wrap",
      }}>
        {msg.content}
        {msg.tool_calls && msg.tool_calls.length > 0 && (
          <div style={{ marginTop: 10, borderTop: "1px solid #2A2E37", paddingTop: 8 }}>
            {msg.tool_calls.map((tc, i) => (
              <ToolCallChip key={i} tc={tc} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolCallChip({ tc }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ marginBottom: 4, fontSize: 12 }}>
      <button type="button" onClick={() => setOpen(v => !v)}
        style={{ background: "#1e3a5f", border: "none", borderRadius: 6, padding: "3px 10px", color: "#60A5FA", cursor: "pointer", fontSize: 12, fontWeight: 600 }}>
        {open ? "▾" : "▸"} {tc.name}
      </button>
      {open && (
        <div style={{ marginTop: 4, background: "#0D1117", borderRadius: 6, padding: "8px 10px", border: "1px solid #2A2E37" }}>
          <div style={{ color: "#9AA2B1", marginBottom: 4 }}>Input:</div>
          <pre style={{ margin: 0, fontSize: 11, color: "#7DD3FC", whiteSpace: "pre-wrap", overflowWrap: "break-word" }}>{JSON.stringify(tc.input, null, 2)}</pre>
          {tc.result !== undefined && (
            <>
              <div style={{ color: "#9AA2B1", marginTop: 6, marginBottom: 4 }}>Result:</div>
              <pre style={{ margin: 0, fontSize: 11, color: "#86EFAC", whiteSpace: "pre-wrap", overflowWrap: "break-word" }}>{typeof tc.result === "string" ? tc.result : JSON.stringify(tc.result, null, 2)}</pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function TypingDots() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4, padding: "10px 14px", background: "var(--bg-surface)", borderRadius: "4px 16px 16px 16px", border: "1px solid var(--border-subtle)", width: "fit-content" }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: 7, height: 7, borderRadius: "50%", background: "#60A5FA",
          animation: `typingPulse 1.2s ${i * 0.2}s ease-in-out infinite`,
        }} />
      ))}
      <style>{`@keyframes typingPulse { 0%,80%,100%{opacity:.3;transform:scale(1)} 40%{opacity:1;transform:scale(1.2)} }`}</style>
    </div>
  );
}

// Build a flat option list: agents + fixed modes
function buildOptions(demoAgents, customAgents, projectName) {
  const opts = [];
  demoAgents.forEach(a => opts.push({ value: `agent:${a.id}`, label: `${a.icon} ${a.name}`, group: "Demo Agents" }));
  customAgents.forEach(a => opts.push({ value: `agent:${a.id}`, label: `${(a.icon ?? "🤖")} ${a.name}`, group: projectName }));
  opts.push({ value: "graph", label: "🕸️ Knowledge Graph", group: "Direct" });
  opts.push({ value: "model", label: "🤖 Direct Model (no tools)", group: "Direct" });
  return opts;
}

export function ChatScreen() {
  const { activeProject, mcpServers } = useProject();
  const customAgents = activeProject.agents ?? [];
  const allAgents = [...DEMO_AGENTS, ...customAgents];

  const [selection, setSelection] = useState(`agent:${DEMO_AGENTS[0].id}`);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  // Derive mode + agent from the single selection string
  const isAgent = selection.startsWith("agent:");
  const isGraph = selection === "graph";
  const selectedAgent = isAgent ? allAgents.find(a => a.id === selection.slice(6)) : null;

  const activeSystemPrompt = isAgent
    ? (selectedAgent?.systemPrompt ?? "You are a helpful assistant.")
    : isGraph
    ? "You are a knowledge graph query assistant. Use the graph, entity and sources tools to answer questions."
    : "You are a helpful assistant.";

  const activeTools = selection === "model"
    ? []
    : isGraph
    ? ["get_graph", "get_entity", "list_sources"]
    : (selectedAgent?.tools ?? ["search_context", "get_graph", "get_entity", "list_sources"]);

  const activeModel = selectedAgent?.model ?? "claude-sonnet-4-5";

  const options = buildOptions(DEMO_AGENTS, customAgents, activeProject.name);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");

    const userMsg = { role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const history = [...messages, userMsg].map(m => ({
        role: m.role === "error" ? "user" : m.role,
        content: m.content,
      }));
      const res = await agentChat({
        messages: history,
        system_prompt: activeSystemPrompt,
        model: activeModel,
        enabled_tools: activeTools,
        extra_tool_servers: mcpServers ?? [],
      });
      setMessages(prev => [...prev, {
        role: "assistant",
        content: res.answer,
        tool_calls: res.tool_calls ?? [],
      }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "error", content: e.message }]);
    } finally {
      setLoading(false);
    }
  }

  const currentLabel = options.find(o => o.value === selection)?.label ?? selection;

  return (
    <div style={{ display: "flex", height: "calc(100vh - 56px - 48px)", maxWidth: 900, margin: "0 auto", flexDirection: "column" }}>
      {/* Header row: title + single dropdown + clear */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14, flexShrink: 0 }}>
        <h1 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", margin: 0, flexShrink: 0 }}>Chat</h1>

        {/* Unified selector */}
        <div style={{ position: "relative", flex: 1, maxWidth: 300 }}>
          <select
            value={selection}
            onChange={e => { setSelection(e.target.value); setMessages([]); }}
            style={{
              width: "100%", appearance: "none", WebkitAppearance: "none",
              padding: "8px 32px 8px 14px", borderRadius: 10, fontSize: 13, fontWeight: 600,
              background: "var(--bg-surface)", color: "var(--text-primary)",
              border: "1px solid var(--border-subtle)", cursor: "pointer", outline: "none",
            }}>
            {/* Group by label */}
            {["Demo Agents", activeProject.name, "Direct"].map(group => {
              const items = options.filter(o => o.group === group);
              if (!items.length) return null;
              return (
                <optgroup key={group} label={group}>
                  {items.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </optgroup>
              );
            })}
          </select>
          <span style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", pointerEvents: "none", color: "var(--text-secondary)", fontSize: 11 }}>▾</span>
        </div>

        {/* Tools / model info chip */}
        <div style={{ fontSize: 11, color: "var(--text-secondary)", background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 20, padding: "4px 10px", whiteSpace: "nowrap" }}>
          {activeTools.length ? `${activeTools.length} tools` : "no tools"} · {activeModel}
        </div>

        <div style={{ flex: 1 }} />
        <button type="button" onClick={() => setMessages([])}
          style={{ background: "var(--bg-canvas)", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "6px 12px", color: "var(--text-secondary)", fontSize: 12, cursor: "pointer", flexShrink: 0 }}>
          Clear
        </button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "4px 0", minHeight: 0 }}>
        {messages.map((m, i) => <MsgBubble key={i} msg={m} />)}
        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, margin: "6px 0" }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", background: "#2563EB", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, flexShrink: 0 }}>🧠</div>
            <TypingDots />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div style={{ flexShrink: 0, paddingTop: 12 }}>
        <div style={{ display: "flex", gap: 8, background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 12, padding: "8px 12px", alignItems: "flex-end" }}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder="Ask a question… (Enter to send, Shift+Enter for newline)"
            rows={1}
            style={{
              flex: 1, background: "none", border: "none", outline: "none", resize: "none",
              color: "var(--text-primary)", fontSize: 14, fontFamily: "inherit", lineHeight: 1.5,
              maxHeight: 120, overflow: "auto",
            }}
          />
          <button type="button" onClick={send} disabled={loading || !input.trim()}
            style={{ background: loading || !input.trim() ? "#334155" : "#2563EB", color: "#fff", border: "none", borderRadius: 8, padding: "8px 16px", fontWeight: 600, fontSize: 13, cursor: loading || !input.trim() ? "not-allowed" : "pointer", flexShrink: 0 }}>
            Send
          </button>
        </div>
        <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 4, textAlign: "center" }}>
          {currentLabel} · Requires ANTHROPIC_API_KEY in .env
        </div>
      </div>
    </div>
  );
}
