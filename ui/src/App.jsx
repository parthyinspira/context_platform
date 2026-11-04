import { useEffect, useState } from "react";
import { NavRail } from "./components/NavRail.jsx";
import { TopBar } from "./components/TopBar.jsx";
import { SourcesScreen } from "./components/SourcesScreen.jsx";
import { RunView } from "./components/RunView.jsx";
import { ValidationReportScreen } from "./components/ValidationReportScreen.jsx";
import { GraphScreen } from "./components/GraphScreen.jsx";
import { AgentsScreen } from "./components/AgentsScreen.jsx";
import { MCPScreen } from "./components/MCPScreen.jsx";
import { PipelinesScreen } from "./components/PipelinesScreen.jsx";
import { ModelsScreen, ChunkingScreen, ExtractionScreen, ProjectSettingsScreen } from "./components/SettingsScreen.jsx";
import { MCPSettingsScreen } from "./components/MCPSettingsScreen.jsx";
import { ChatScreen } from "./components/ChatScreen.jsx";
import { applyTheme } from "./theme.js";

const NAV_TO_VIEW = {
  Graph:               "graph",
  Pipelines:           "pipelines",
  Sources:             "sources",
  Agents:              "agents",
  Chat:                "chat",
  MCP:                 "mcp",
  SettingsMCP:         "settings-mcp",
  SettingsModels:      "settings-models",
  SettingsChunking:    "settings-chunking",
  SettingsExtraction:  "settings-extraction",
  SettingsProject:     "settings-project",
};

export function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("cp-theme") ?? "dark");
  const [view, setView] = useState("graph");
  const [activeRun, setActiveRun] = useState(null);
  const [activeValidationRunId, setActiveValidationRunId] = useState(null);

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem("cp-theme", theme);
  }, [theme]);

  function handleNavigate(item) {
    setView(NAV_TO_VIEW[item] ?? "graph");
  }

  function handleRunStarted(run) {
    setActiveRun(run);
    setView("run");
  }

  const activeNavItem =
    view === "sources" || view === "run" || view === "validation" ? "Sources"
    : view === "pipelines" ? "Pipelines"
    : view === "agents" ? "Agents"
    : view === "chat" ? "Chat"
    : view === "mcp" ? "MCP"
    : view === "settings-mcp" ? "SettingsMCP"
    : view === "settings-models" ? "SettingsModels"
    : view === "settings-chunking" ? "SettingsChunking"
    : view === "settings-extraction" ? "SettingsExtraction"
    : view === "settings-project" ? "SettingsProject"
    : "Graph";

  return (
    <div className="flex h-full bg-bg-canvas text-text-primary">
      <NavRail active={activeNavItem} onNavigate={handleNavigate} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          theme={theme}
          onToggleTheme={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
        />
        <main className="p-6" style={{ flex: 1, minHeight: 0, overflow: "auto" }}>
          {view === "graph" && <GraphScreen onAddSource={() => setView("sources")} />}
          {view === "pipelines" && <PipelinesScreen onViewRun={(runId) => { setActiveRun({ id: runId }); setView("run"); }} />}
          {view === "agents" && <AgentsScreen />}
          {view === "chat" && <ChatScreen />}
          {view === "mcp" && <MCPScreen />}
          {view === "settings-mcp" && <MCPSettingsScreen />}
          {view === "settings-models" && <ModelsScreen />}
          {view === "settings-chunking" && <ChunkingScreen />}
          {view === "settings-extraction" && <ExtractionScreen />}
          {view === "settings-project" && <ProjectSettingsScreen />}
          {view === "sources" && <SourcesScreen onRunStarted={handleRunStarted} />}
          {view === "run" && activeRun && (
            <RunView
              run={activeRun}
              onViewValidationReport={(runId) => {
                setActiveValidationRunId(runId);
                setView("validation");
              }}
              onBackToSources={() => setView("sources")}
            />
          )}
          {view === "validation" && activeValidationRunId && (
            <ValidationReportScreen
              runId={activeValidationRunId}
              onBack={() => setView("run")}
            />
          )}
        </main>
      </div>
    </div>
  );
}
