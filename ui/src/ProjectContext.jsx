import { createContext, useContext, useState, useCallback } from "react";

const STORAGE_KEY = "context_platform_projects_v1";
const MCP_STORAGE_KEY = "cp_mcp_servers_v1";

const PROJECT_ICONS = ["🏥", "💳", "🏦", "🛒", "🏢", "🔬", "⚡", "🌐", "📊", "🚀"];
const PROJECT_COLORS = ["#2563EB", "#059669", "#7C3AED", "#D97706", "#DC2626", "#0891B2"];

const DEFAULT_SETTINGS = {
  llmProvider: "anthropic",
  llmApiKey: "",
  llmModel: "claude-sonnet-4-5",
  llmEndpoint: "",
  embedProvider: "local",
  embedModel: "all-MiniLM-L6-v2",
  embedApiKey: "",
  chunkStrategy: "structural",
  chunkSize: 512,
  chunkOverlap: 64,
  graphExtraction: "rule",
  graphConfidenceThreshold: 0.7,
  graphAutoApplyThreshold: 0.9,
  graphLLMCitations: true,
  graphMaxHopsDisplay: 3,
};

function newProject(name, icon, color) {
  return {
    id: crypto.randomUUID(),
    name,
    icon: icon ?? PROJECT_ICONS[0],
    color: color ?? PROJECT_COLORS[0],
    createdAt: new Date().toISOString(),
    settings: { ...DEFAULT_SETTINGS },
    agents: [],
  };
}

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function persist(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function initialState() {
  const saved = load();
  if (saved?.projects?.length) return saved;
  const defaultProject = newProject("Default Project", "🏢", "#2563EB");
  return { projects: [defaultProject], activeId: defaultProject.id };
}

// ── Context ───────────────────────────────────────────────────────────────────

const ProjectContext = createContext(null);

export function ProjectProvider({ children }) {
  const [state, setState] = useState(initialState);
  const [mcpServers, setMcpServers] = useState(() => {
    try { return JSON.parse(localStorage.getItem(MCP_STORAGE_KEY) ?? "[]"); } catch { return []; }
  });

  const addMcpServer = useCallback((url) => {
    setMcpServers(prev => {
      if (prev.includes(url)) return prev;
      const next = [...prev, url];
      localStorage.setItem(MCP_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const removeMcpServer = useCallback((url) => {
    setMcpServers(prev => {
      const next = prev.filter(u => u !== url);
      localStorage.setItem(MCP_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const activeProject = state.projects.find((p) => p.id === state.activeId) ?? state.projects[0];

  const setActive = useCallback((id) => {
    setState((prev) => {
      const next = { ...prev, activeId: id };
      persist(next);
      return next;
    });
  }, []);

  const createProject = useCallback((name, icon, color) => {
    const p = newProject(name, icon, color);
    setState((prev) => {
      const next = { projects: [...prev.projects, p], activeId: p.id };
      persist(next);
      return next;
    });
    return p;
  }, []);

  const updateProjectSettings = useCallback((projectId, settings) => {
    setState((prev) => {
      const next = {
        ...prev,
        projects: prev.projects.map((p) =>
          p.id === projectId ? { ...p, settings: { ...p.settings, ...settings } } : p
        ),
      };
      persist(next);
      return next;
    });
  }, []);

  const updateProjectMeta = useCallback((projectId, meta) => {
    setState((prev) => {
      const next = {
        ...prev,
        projects: prev.projects.map((p) =>
          p.id === projectId ? { ...p, ...meta } : p
        ),
      };
      persist(next);
      return next;
    });
  }, []);

  const saveAgent = useCallback((projectId, agent) => {
    setState((prev) => {
      const next = {
        ...prev,
        projects: prev.projects.map((p) => {
          if (p.id !== projectId) return p;
          const agents = p.agents ?? [];
          const exists = agents.findIndex((a) => a.id === agent.id);
          return { ...p, agents: exists >= 0 ? agents.map((a) => a.id === agent.id ? agent : a) : [...agents, agent] };
        }),
      };
      persist(next);
      return next;
    });
  }, []);

  const deleteAgent = useCallback((projectId, agentId) => {
    setState((prev) => {
      const next = {
        ...prev,
        projects: prev.projects.map((p) =>
          p.id !== projectId ? p : { ...p, agents: (p.agents ?? []).filter((a) => a.id !== agentId) }
        ),
      };
      persist(next);
      return next;
    });
  }, []);

  const deleteProject = useCallback((projectId) => {
    setState((prev) => {
      if (prev.projects.length <= 1) return prev;
      const projects = prev.projects.filter((p) => p.id !== projectId);
      const activeId = prev.activeId === projectId ? projects[0].id : prev.activeId;
      const next = { projects, activeId };
      persist(next);
      return next;
    });
  }, []);

  return (
    <ProjectContext.Provider value={{
      projects: state.projects,
      activeProject,
      setActive,
      createProject,
      updateProjectSettings,
      updateProjectMeta,
      deleteProject,
      saveAgent,
      deleteAgent,
      mcpServers,
      addMcpServer,
      removeMcpServer,
      PROJECT_ICONS,
      PROJECT_COLORS,
      DEFAULT_SETTINGS,
    }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProject must be used inside <ProjectProvider>");
  return ctx;
}
