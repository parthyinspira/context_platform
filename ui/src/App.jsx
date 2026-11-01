import { useEffect, useState } from "react";
import { NavRail } from "./components/NavRail.jsx";
import { TopBar } from "./components/TopBar.jsx";
import { SourcesScreen } from "./components/SourcesScreen.jsx";
import { RunView } from "./components/RunView.jsx";
import { ValidationReportScreen } from "./components/ValidationReportScreen.jsx";
import { GraphScreen } from "./components/GraphScreen.jsx";
import { AgentsScreen } from "./components/AgentsScreen.jsx";
import { applyTheme } from "./theme.js";

const NAV_TO_VIEW = {
  Graph: "graph",
  Sources: "sources",
  Runs: "graph",
  Agents: "agents",
  Settings: "graph",
};

export function App() {
  const [theme, setTheme] = useState("light");
  const [view, setView] = useState("graph");
  const [activeRun, setActiveRun] = useState(null);
  const [activeValidationRunId, setActiveValidationRunId] = useState(null);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  function handleNavigate(item) {
    setView(NAV_TO_VIEW[item] ?? "graph");
  }

  function handleRunStarted(run) {
    setActiveRun(run);
    setView("run");
  }

  const activeNavItem =
    view === "sources" || view === "run" || view === "validation"
      ? "Sources"
      : view === "agents"
        ? "Agents"
        : "Graph";

  return (
    <div className="flex h-full bg-bg-canvas text-text-primary">
      <NavRail active={activeNavItem} onNavigate={handleNavigate} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          theme={theme}
          onToggleTheme={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
        />
        <main className="p-6">
          {view === "graph" && <GraphScreen />}
          {view === "agents" && <AgentsScreen />}
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
