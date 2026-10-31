import { useEffect, useState } from "react";
import { NavRail } from "./components/NavRail.jsx";
import { TopBar } from "./components/TopBar.jsx";
import { applyTheme } from "./theme.js";

export function App() {
  const [theme, setTheme] = useState("light");

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  return (
    <div className="app-shell">
      <NavRail active="Graph" />
      <div className="app-main">
        <TopBar
          theme={theme}
          onToggleTheme={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
        />
        <main className="app-content">
          <p>Context Platform</p>
        </main>
      </div>
    </div>
  );
}
