import { useState } from "react";
import { useProject } from "../ProjectContext.jsx";

const NAV_ITEMS = [
  { key: "Graph",     label: "Knowledge Graph" },
  { key: "Pipelines", label: "Pipelines" },
  { key: "Sources",   label: "Sources" },
  { key: "Agents",    label: "Agents" },
  { key: "Chat",      label: "Chat" },
  { key: "MCP",       label: "MCP Tools" },
];

const SETTINGS_ITEMS = [
  { key: "SettingsMCP",        label: "MCP" },
  { key: "SettingsModels",     label: "Models" },
  { key: "SettingsChunking",   label: "Chunking" },
  { key: "SettingsExtraction", label: "Extraction" },
  { key: "SettingsProject",    label: "Project" },
];

const SETTINGS_KEYS = new Set(SETTINGS_ITEMS.map((s) => s.key));

function ProjectSwitcher() {
  const { projects, activeProject, setActive, createProject, deleteProject, PROJECT_ICONS, PROJECT_COLORS } = useProject();
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newIcon, setNewIcon] = useState(PROJECT_ICONS[0]);
  const [newColor, setNewColor] = useState(PROJECT_COLORS[0]);

  function handleCreate() {
    if (!newName.trim()) return;
    createProject(newName.trim(), newIcon, newColor);
    setNewName(""); setNewIcon(PROJECT_ICONS[0]); setNewColor(PROJECT_COLORS[0]);
    setCreating(false); setOpen(false);
  }

  return (
    <div style={{ position: "relative", padding: "8px 12px 6px" }}>
      <button type="button" onClick={() => setOpen((v) => !v)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: 9, padding: "9px 12px", borderRadius: 8, border: "1px solid var(--border-subtle)", background: "var(--bg-canvas)", cursor: "pointer", textAlign: "left" }}>
        <div style={{ width: 24, height: 24, borderRadius: 6, flexShrink: 0, background: activeProject.color, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>
          {activeProject.icon}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{activeProject.name}</div>
          <div style={{ fontSize: 10, color: "var(--text-secondary)" }}>Switch project ▾</div>
        </div>
      </button>

      {open && (
        <div style={{ position: "absolute", top: "calc(100% + 2px)", left: 12, right: 12, background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 10, boxShadow: "0 8px 24px rgba(0,0,0,.2)", zIndex: 100, overflow: "hidden" }}>
          {projects.map((p) => (
            <div key={p.id}
              style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 12px", cursor: "pointer", background: p.id === activeProject.id ? "var(--accent)22" : "transparent", borderBottom: "1px solid var(--border-subtle)" }}
              onClick={() => { setActive(p.id); setOpen(false); }}>
              <div style={{ width: 22, height: 22, borderRadius: 5, background: p.color, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, flexShrink: 0 }}>{p.icon}</div>
              <span style={{ flex: 1, fontSize: 12, fontWeight: 600, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.name}</span>
              {p.id === activeProject.id && <span style={{ fontSize: 11, color: "#2563EB" }}>✓</span>}
              {projects.length > 1 && p.id !== activeProject.id && (
                <button type="button" onClick={(e) => { e.stopPropagation(); deleteProject(p.id); }}
                  style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", fontSize: 13, padding: "0 2px" }}>✕</button>
              )}
            </div>
          ))}
          {!creating ? (
            <button type="button" onClick={() => setCreating(true)}
              style={{ width: "100%", padding: "9px 12px", border: "none", background: "transparent", color: "#2563EB", fontWeight: 600, fontSize: 12, cursor: "pointer", textAlign: "left" }}>
              + New project
            </button>
          ) : (
            <div style={{ padding: "10px 12px", borderTop: "1px solid var(--border-subtle)" }}>
              <input autoFocus type="text" value={newName} onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleCreate(); if (e.key === "Escape") setCreating(false); }}
                placeholder="Project name"
                style={{ width: "100%", boxSizing: "border-box", border: "1px solid var(--border-subtle)", background: "var(--bg-canvas)", color: "var(--text-primary)", borderRadius: 6, padding: "6px 8px", fontSize: 12, marginBottom: 8, outline: "none" }} />
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 8 }}>
                {PROJECT_ICONS.map((ic) => (
                  <button key={ic} type="button" onClick={() => setNewIcon(ic)}
                    style={{ width: 26, height: 26, borderRadius: 5, border: `2px solid ${ic === newIcon ? "#2563EB" : "transparent"}`, background: "var(--bg-canvas)", fontSize: 14, cursor: "pointer" }}>{ic}</button>
                ))}
              </div>
              <div style={{ display: "flex", gap: 4, marginBottom: 10 }}>
                {PROJECT_COLORS.map((c) => (
                  <button key={c} type="button" onClick={() => setNewColor(c)}
                    style={{ width: 20, height: 20, borderRadius: "50%", border: `2px solid ${c === newColor ? "var(--text-primary)" : "transparent"}`, background: c, cursor: "pointer" }} />
                ))}
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                <button type="button" onClick={handleCreate}
                  style={{ flex: 1, background: "#2563EB", color: "#fff", border: "none", borderRadius: 6, padding: "6px 0", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>Create</button>
                <button type="button" onClick={() => setCreating(false)}
                  style={{ flex: 1, background: "var(--bg-canvas)", color: "var(--text-secondary)", border: "1px solid var(--border-subtle)", borderRadius: 6, padding: "6px 0", fontSize: 12, cursor: "pointer" }}>Cancel</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function NavBtn({ label, active, onClick }) {
  return (
    <li>
      <button type="button" onClick={onClick}
        style={{
          width: "100%",
          padding: "9px 16px",
          borderRadius: 8,
          border: "none",
          background: active ? "#2563EB" : "transparent",
          color: active ? "#ffffff" : "var(--text-secondary)",
          fontWeight: active ? 600 : 400,
          fontSize: 13,
          cursor: "pointer",
          textAlign: "left",
          marginBottom: 2,
          transition: "background 0.15s",
        }}
        onMouseEnter={e => { if (!active) e.currentTarget.style.background = "var(--border-subtle)"; }}
        onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
      >
        {label}
      </button>
    </li>
  );
}

export function NavRail({ active = "Graph", onNavigate }) {
  return (
    <nav data-testid="nav-rail"
      style={{ width: 220, flexShrink: 0, display: "flex", flexDirection: "column", background: "var(--bg-surface)", borderRight: "1px solid var(--border-subtle)", height: "100%" }}>

      {/* Logo / App title */}
      <div style={{ padding: "20px 20px 14px", borderBottom: "1px solid var(--border-subtle)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: 9, background: "#2563EB", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>🧠</div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>Context</div>
            <div style={{ fontSize: 12, fontWeight: 400, color: "var(--text-secondary)" }}>Platform</div>
          </div>
        </div>
      </div>

      {/* Project switcher */}
      <ProjectSwitcher />
      <div style={{ height: 1, background: "var(--border-subtle)", margin: "4px 12px 6px" }} />

      {/* Main nav */}
      <ul style={{ listStyle: "none", margin: 0, padding: "0 10px" }}>
        {NAV_ITEMS.map(({ key, label }) => (
          <NavBtn key={key} label={label} active={key === active} onClick={() => onNavigate?.(key)} />
        ))}
      </ul>

      {/* Settings section */}
      <div style={{ margin: "16px 10px 0" }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".1em", padding: "0 6px 6px", opacity: 0.6 }}>
          Settings
        </div>
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {SETTINGS_ITEMS.map(({ key, label }) => (
            <NavBtn key={key} label={label} active={key === active} onClick={() => onNavigate?.(key)} />
          ))}
        </ul>
      </div>

      <div style={{ flex: 1 }} />
      <div style={{ padding: "12px 20px", borderTop: "1px solid var(--border-subtle)" }}>
        <div style={{ fontSize: 11, color: "var(--text-secondary)", opacity: 0.6 }}>Hackathon build · v0.1</div>
      </div>
    </nav>
  );
}
