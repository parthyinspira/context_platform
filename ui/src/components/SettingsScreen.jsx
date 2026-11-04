import { useState } from "react";
import { useProject } from "../ProjectContext.jsx";

// ── Shared primitives ─────────────────────────────────────────────────────────

export function SectionCard({ icon, title, subtitle, children }) {
  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 14, padding: "24px 28px", marginBottom: 20 }}>
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 24 }}>{icon}</span>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>{title}</h2>
        </div>
        {subtitle && <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: "4px 0 0 34px" }}>{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export function Field({ label, hint, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>{label}</label>
      {hint && <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 6 }}>{hint}</div>}
      {children}
    </div>
  );
}

export function TextInput({ value, onChange, placeholder, type = "text", mono = false }) {
  return (
    <input type={type} value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)}
      style={{ width: "100%", boxSizing: "border-box", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "9px 12px", fontSize: 13, fontFamily: mono ? "monospace" : "inherit", outline: "none" }} />
  );
}

export function Select({ value, onChange, options }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
      style={{ width: "100%", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "9px 12px", fontSize: 13, outline: "none" }}>
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

export function Slider({ value, onChange, min, max, step = 1, formatLabel }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} style={{ flex: 1, accentColor: "#2563EB" }} />
      <span style={{ minWidth: 60, textAlign: "right", fontSize: 13, fontWeight: 600, color: "var(--accent)", fontFamily: "monospace" }}>
        {formatLabel ? formatLabel(value) : value}
      </span>
    </div>
  );
}

export function Toggle({ value, onChange, label }) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
      <div onClick={() => onChange(!value)}
        style={{ width: 42, height: 24, borderRadius: 12, background: value ? "#2563EB" : "var(--border-subtle)", position: "relative", transition: "background .2s", cursor: "pointer" }}>
        <div style={{ position: "absolute", top: 3, left: value ? 20 : 3, width: 18, height: 18, borderRadius: "50%", background: "#fff", transition: "left .2s", boxShadow: "0 1px 3px rgba(0,0,0,.2)" }} />
      </div>
      <span style={{ fontSize: 13, color: "var(--text-primary)" }}>{label}</span>
    </label>
  );
}

function InfoBox({ color = "blue", children }) {
  const styles = {
    blue:   { bg: "#1e3a5f", border: "#2563EB44", text: "#93C5FD" },
    green:  { bg: "#052e16", border: "#05966944", text: "#6EE7B7" },
    yellow: { bg: "#1c1a05", border: "#D9770644", text: "#FCD34D" },
  };
  const s = styles[color];
  return <div style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: 8, padding: "10px 14px", fontSize: 12, color: s.text, marginTop: 12 }}>{children}</div>;
}

function SaveBar({ onSave, saved, label = "Save settings" }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 4 }}>
      <button type="button" onClick={onSave}
        style={{ background: "#2563EB", color: "#fff", border: "none", borderRadius: 9, padding: "11px 28px", fontWeight: 700, fontSize: 15, cursor: "pointer" }}>
        💾 {label}
      </button>
      {saved && <span style={{ color: "var(--success)", fontWeight: 600, fontSize: 14 }}>✓ Saved</span>}
      <span style={{ color: "var(--text-secondary)", fontSize: 12, marginLeft: "auto" }}>Stored per project in browser.</span>
    </div>
  );
}

function useDraft() {
  const { activeProject, updateProjectSettings } = useProject();
  const [draft, setDraft] = useState(() => ({ ...activeProject.settings }));
  const [saved, setSaved] = useState(false);
  const [lastId, setLastId] = useState(activeProject.id);

  if (activeProject.id !== lastId) {
    setLastId(activeProject.id);
    setDraft({ ...activeProject.settings });
    setSaved(false);
  }

  function set(key, value) { setDraft((p) => ({ ...p, [key]: value })); setSaved(false); }
  function save() { updateProjectSettings(activeProject.id, draft); setSaved(true); setTimeout(() => setSaved(false), 2500); }

  return { draft, set, save, saved };
}

// ── LLM provider metadata ─────────────────────────────────────────────────────

const LLM_PROVIDERS = [
  { value: "anthropic", label: "🧠 Anthropic (Claude)", keyLabel: "API key", keyHint: "sk-ant-…", models: ["claude-sonnet-4-5", "claude-haiku-4-5", "claude-opus-4-5"] },
  { value: "openai",    label: "⚡ OpenAI / Compatible", keyLabel: "API key", keyHint: "sk-…",     models: ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"] },
  { value: "meta",      label: "🦙 Meta Llama (hackathon credits)", keyLabel: "Endpoint URL", keyHint: "https://…", models: ["meta-llama/Llama-3.1-70B-Instruct", "meta-llama/Llama-3.1-8B-Instruct"] },
  { value: "ollama",    label: "💻 Ollama (local)", keyLabel: "Base URL", keyHint: "http://localhost:11434", models: ["llama3.2", "mistral", "phi3"] },
  { value: "vertex",    label: "☁️ Google Vertex AI", keyLabel: "Project ID", keyHint: "my-gcp-project", models: ["gemini-1.5-pro", "gemini-1.5-flash"] },
  { value: "azure",     label: "🔷 Azure AI Foundry", keyLabel: "Endpoint URL", keyHint: "https://…openai.azure.com/", models: ["gpt-4o", "gpt-4-turbo"] },
];

const EMBED_PROVIDERS = [
  { value: "local",  label: "💻 Local (sentence-transformers / Ollama)" },
  { value: "openai", label: "⚡ OpenAI Embeddings" },
  { value: "vertex", label: "☁️ Google Vertex Embeddings" },
  { value: "azure",  label: "🔷 Azure Embedding Model" },
];

// ── Tab screens ───────────────────────────────────────────────────────────────

export function ModelsScreen() {
  const { draft, set, save, saved } = useDraft();
  const llmMeta = LLM_PROVIDERS.find((p) => p.value === draft.llmProvider) ?? LLM_PROVIDERS[0];

  return (
    <div style={{ maxWidth: 740 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>🧠 Models</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: "4px 0 0" }}>Configure which LLM and embedding model this project uses for entity extraction and semantic search.</p>
      </div>

      <SectionCard icon="🤖" title="LLM Provider" subtitle="Used for entity extraction from unstructured text (READMEs, comments, docs)">
        <Field label="Provider">
          <Select value={draft.llmProvider} onChange={(v) => set("llmProvider", v)} options={LLM_PROVIDERS.map((p) => ({ value: p.value, label: p.label }))} />
        </Field>
        <Field label={llmMeta.keyLabel} hint={`Format: ${llmMeta.keyHint}`}>
          <TextInput type="password" value={draft.llmApiKey} onChange={(v) => set("llmApiKey", v)} placeholder={llmMeta.keyHint} mono />
        </Field>
        {["meta", "ollama", "azure"].includes(draft.llmProvider) && (
          <Field label="Endpoint URL">
            <TextInput value={draft.llmEndpoint} onChange={(v) => set("llmEndpoint", v)} placeholder={llmMeta.keyHint} />
          </Field>
        )}
        <Field label="Model">
          <Select value={draft.llmModel} onChange={(v) => set("llmModel", v)} options={llmMeta.models.map((m) => ({ value: m, label: m }))} />
        </Field>
        <InfoBox color="blue">🔒 API keys are stored in your browser only and sent only to your local API service — never to any third party. For production, use environment variables or your SecretStore. Contact <strong>security@inspirafinancial.com</strong> for security controls.</InfoBox>
      </SectionCard>

      <SectionCard icon="🔢" title="Embedding Provider" subtitle="Generates vector embeddings for semantic similarity search in the knowledge graph">
        <Field label="Provider">
          <Select value={draft.embedProvider} onChange={(v) => set("embedProvider", v)} options={EMBED_PROVIDERS.map((p) => ({ value: p.value, label: p.label }))} />
        </Field>
        <Field label="Model name" hint="e.g. all-MiniLM-L6-v2 (local) · text-embedding-3-small (OpenAI)">
          <TextInput value={draft.embedModel} onChange={(v) => set("embedModel", v)} placeholder="all-MiniLM-L6-v2" mono />
        </Field>
        {draft.embedProvider !== "local" && (
          <Field label="API key">
            <TextInput type="password" value={draft.embedApiKey} onChange={(v) => set("embedApiKey", v)} placeholder="sk-…" mono />
          </Field>
        )}
      </SectionCard>

      <SaveBar onSave={save} saved={saved} />
    </div>
  );
}

const CHUNK_STRATEGIES = [
  { value: "structural", label: "Structural — by function / section / table (recommended)" },
  { value: "paragraph",  label: "Paragraph — split at blank lines" },
  { value: "fixed",      label: "Fixed window — fixed token count with overlap" },
];

export function ChunkingScreen() {
  const { draft, set, save, saved } = useDraft();

  return (
    <div style={{ maxWidth: 740 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>✂️ Chunking</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: "4px 0 0" }}>Control how harvested content is split into chunks before embedding and indexing.</p>
      </div>

      <SectionCard icon="✂️" title="Chunking Strategy" subtitle="Applies to all sources in this project">
        <Field label="Strategy">
          <Select value={draft.chunkStrategy} onChange={(v) => set("chunkStrategy", v)} options={CHUNK_STRATEGIES} />
        </Field>

        {draft.chunkStrategy === "fixed" && (
          <>
            <Field label={`Chunk size — ${draft.chunkSize} tokens`} hint="Maximum tokens per chunk">
              <Slider value={draft.chunkSize} onChange={(v) => set("chunkSize", v)} min={128} max={2048} step={64} formatLabel={(v) => `${v} tok`} />
            </Field>
            <Field label={`Overlap — ${draft.chunkOverlap} tokens`} hint="Tokens shared between adjacent chunks to preserve context at boundaries">
              <Slider value={draft.chunkOverlap} onChange={(v) => set("chunkOverlap", v)} min={0} max={256} step={16} formatLabel={(v) => `${v} tok`} />
            </Field>
          </>
        )}

        {draft.chunkStrategy === "structural" && (
          <InfoBox color="green">✅ Structural chunking splits code at function/class boundaries, documents at headings, tables at row boundaries — no manual size tuning needed. This is the recommended default.</InfoBox>
        )}
        {draft.chunkStrategy === "paragraph" && (
          <InfoBox color="green">✅ Paragraph chunking splits on blank lines. Good for prose documentation and markdown files.</InfoBox>
        )}
      </SectionCard>

      <SectionCard icon="📏" title="Size Limits" subtitle="Per-chunk hard limits regardless of strategy">
        <Field label="Max chunk size (tokens)" hint="Chunks larger than this are split further, regardless of strategy">
          <Slider value={draft.chunkSize} onChange={(v) => set("chunkSize", v)} min={128} max={4096} step={64} formatLabel={(v) => `${v} tok`} />
        </Field>
      </SectionCard>

      <SaveBar onSave={save} saved={saved} />
    </div>
  );
}

const GRAPH_EXTRACTIONS = [
  { value: "rule", label: "Rule-based only — deterministic (manifests, SQL lineage, CODEOWNERS)" },
  { value: "llm",  label: "LLM only — broader but needs an API key" },
  { value: "both", label: "Rule-based + LLM — most complete coverage" },
];

export function ExtractionScreen() {
  const { draft, set, save, saved } = useDraft();

  return (
    <div style={{ maxWidth: 740 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>🕸️ Extraction</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: "4px 0 0" }}>Control how entities and relationships are extracted and added to the knowledge graph.</p>
      </div>

      <SectionCard icon="⚗️" title="Extraction Method" subtitle="How entities and relationships are found in harvested content">
        <Field label="Method">
          <Select value={draft.graphExtraction} onChange={(v) => set("graphExtraction", v)} options={GRAPH_EXTRACTIONS} />
        </Field>
        {draft.graphExtraction === "rule" && (
          <InfoBox color="green">✅ Rule-based uses deterministic parsers — no LLM key required. Covers: package manifests, SQL lineage via sqlglot, CODEOWNERS, import graphs.</InfoBox>
        )}
        {["llm", "both"].includes(draft.graphExtraction) && !draft.llmApiKey && (
          <InfoBox color="yellow">⚠️ LLM extraction needs an API key — go to <strong>Models</strong> and add one first.</InfoBox>
        )}
        {["llm", "both"].includes(draft.graphExtraction) && (
          <div style={{ marginTop: 14 }}>
            <Toggle value={draft.graphLLMCitations} onChange={(v) => set("graphLLMCitations", v)} label="Require citation for every LLM-extracted fact" />
          </div>
        )}
      </SectionCard>

      <SectionCard icon="🎚️" title="Confidence Thresholds" subtitle="Control which facts are auto-applied vs. sent for review vs. discarded">
        <Field label={`Auto-apply — ${Math.round(draft.graphAutoApplyThreshold * 100)}%`}
          hint="Facts above this confidence are written to the graph immediately">
          <Slider value={draft.graphAutoApplyThreshold} onChange={(v) => set("graphAutoApplyThreshold", v)} min={0.5} max={1.0} step={0.05} formatLabel={(v) => `${Math.round(v * 100)}%`} />
        </Field>
        <Field label={`Review threshold — ${Math.round(draft.graphConfidenceThreshold * 100)}%`}
          hint="Facts between this and auto-apply go to proposed_changes for manual review; facts below are discarded">
          <Slider value={draft.graphConfidenceThreshold} onChange={(v) => set("graphConfidenceThreshold", v)} min={0.1} max={0.9} step={0.05} formatLabel={(v) => `${Math.round(v * 100)}%`} />
        </Field>

        {/* Visual legend */}
        <div style={{ display: "flex", gap: 0, height: 10, borderRadius: 6, overflow: "hidden", marginTop: 8 }}>
          <div style={{ flex: draft.graphConfidenceThreshold, background: "#FEE2E2" }} title="Discard zone" />
          <div style={{ flex: draft.graphAutoApplyThreshold - draft.graphConfidenceThreshold, background: "#FEF3C7" }} title="Review zone" />
          <div style={{ flex: 1 - draft.graphAutoApplyThreshold, background: "#D1FAE5" }} title="Auto-apply zone" />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#9CA3AF", marginTop: 4 }}>
          <span>🔴 Discard</span><span>🟡 Review</span><span>🟢 Auto-apply</span>
        </div>
      </SectionCard>

      <SectionCard icon="🔭" title="Graph Display" subtitle="How the Knowledge Graph view renders results">
        <Field label="Max hops from selected node" hint="Nodes further than this are hidden to avoid clutter">
          <Slider value={draft.graphMaxHopsDisplay} onChange={(v) => set("graphMaxHopsDisplay", v)} min={1} max={6} />
        </Field>
      </SectionCard>

      <SaveBar onSave={save} saved={saved} />
    </div>
  );
}

export function ProjectSettingsScreen() {
  const { activeProject, updateProjectMeta, deleteProject, projects, PROJECT_ICONS, PROJECT_COLORS } = useProject();
  const [name, setName] = useState(activeProject.name);
  const [icon, setIcon] = useState(activeProject.icon);
  const [color, setColor] = useState(activeProject.color);
  const [saved, setSaved] = useState(false);
  const [lastId, setLastId] = useState(activeProject.id);

  if (activeProject.id !== lastId) {
    setLastId(activeProject.id);
    setName(activeProject.name); setIcon(activeProject.icon); setColor(activeProject.color);
    setSaved(false);
  }

  function save() {
    if (!name.trim()) return;
    updateProjectMeta(activeProject.id, { name: name.trim(), icon, color });
    setSaved(true); setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div style={{ maxWidth: 740 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>📁 Project</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: "4px 0 0" }}>Manage this project's identity. Each project has its own sources, runs, and settings.</p>
      </div>

      <SectionCard icon={activeProject.icon} title="Project Identity">
        <Field label="Name">
          <TextInput value={name} onChange={setName} placeholder="Project name" />
        </Field>
        <Field label="Icon">
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {PROJECT_ICONS.map((ic) => (
              <button key={ic} type="button" onClick={() => setIcon(ic)}
                style={{ width: 36, height: 36, borderRadius: 8, border: `2px solid ${ic === icon ? "#2563EB" : "var(--border-subtle)"}`, background: "var(--bg-canvas)", fontSize: 20, cursor: "pointer" }}>
                {ic}
              </button>
            ))}
          </div>
        </Field>
        <Field label="Color">
          <div style={{ display: "flex", gap: 10 }}>
            {PROJECT_COLORS.map((c) => (
              <button key={c} type="button" onClick={() => setColor(c)}
                style={{ width: 30, height: 30, borderRadius: "50%", border: `3px solid ${c === color ? "var(--text-primary)" : "transparent"}`, background: c, cursor: "pointer" }} />
            ))}
          </div>
        </Field>
        <SaveBar onSave={save} saved={saved} label="Save project" />
      </SectionCard>

      {projects.length > 1 && (
        <SectionCard icon="🗑️" title="Danger Zone">
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 0 }}>Deleting a project removes its settings from your browser. Sources and runs in the database are not deleted.</p>
          <button type="button"
            onClick={() => { if (window.confirm(`Delete project "${activeProject.name}"?`)) deleteProject(activeProject.id); }}
            style={{ background: "#DC2626", color: "#fff", border: "none", borderRadius: 8, padding: "9px 20px", fontWeight: 700, fontSize: 14, cursor: "pointer" }}>
            🗑 Delete this project
          </button>
        </SectionCard>
      )}
    </div>
  );
}
