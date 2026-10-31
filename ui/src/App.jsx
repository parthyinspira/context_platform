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
    <div className="flex h-full bg-bg-canvas text-text-primary">
      <NavRail active="Graph" />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          theme={theme}
          onToggleTheme={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
        />
        <main className="p-6">
          <p>Context Platform</p>
        </main>
      </div>
    </div>
  );
}
