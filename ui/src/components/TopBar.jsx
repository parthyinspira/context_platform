export function TopBar({ theme, onToggleTheme }) {
  return (
    <header
      data-testid="top-bar"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        height: 56,
        padding: "0 20px",
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border-subtle)",
        flexShrink: 0,
      }}
    >
      {/* Hamburger */}
      <button type="button" aria-label="Toggle sidebar"
        style={{ background: "none", border: "none", color: "var(--text-secondary)", fontSize: 20, cursor: "pointer", padding: "4px 6px", lineHeight: 1 }}>
        ☰
      </button>

      {/* Search */}
      <div style={{ flex: 1, maxWidth: 500 }}>
        <div style={{ position: "relative" }}>
          <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-secondary)", fontSize: 14 }}>🔍</span>
          <input
            type="search"
            placeholder="Search (/)"
            aria-label="Global search"
            style={{
              width: "100%",
              boxSizing: "border-box",
              paddingLeft: 36,
              paddingRight: 12,
              paddingTop: 8,
              paddingBottom: 8,
              borderRadius: 20,
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-canvas)",
              color: "var(--text-primary)",
              fontSize: 13,
              outline: "none",
            }}
          />
        </div>
      </div>

      <div style={{ flex: 1 }} />

      {/* Notification bell */}
      <div style={{ position: "relative" }}>
        <button type="button" aria-label="Notifications"
          style={{ background: "none", border: "none", color: "var(--text-secondary)", fontSize: 18, cursor: "pointer", padding: "4px 8px", lineHeight: 1 }}>
          🔔
        </button>
        <span style={{ position: "absolute", top: 2, right: 4, width: 16, height: 16, borderRadius: "50%", background: "#DC2626", fontSize: 9, fontWeight: 700, color: "#fff", display: "flex", alignItems: "center", justifyContent: "center" }}>6</span>
      </div>

      {/* Theme toggle */}
      <button
        type="button"
        data-testid="theme-toggle"
        aria-label="Toggle light and dark theme"
        onClick={onToggleTheme}
        style={{ background: "var(--bg-canvas)", border: "1px solid var(--border-subtle)", borderRadius: 8, padding: "6px 12px", color: "var(--text-secondary)", fontSize: 13, cursor: "pointer", fontWeight: 500 }}
      >
        {theme === "dark" ? "🌙 Dark" : "☀️ Light"}
      </button>

      {/* User profile */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "#2563EB", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: "#fff", flexShrink: 0 }}>
          PV
        </div>
        <div style={{ lineHeight: 1.3 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)" }}>Partha</div>
          <div style={{ fontSize: 10, color: "var(--text-secondary)" }}>Admin</div>
        </div>
        <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>▾</span>
      </div>
    </header>
  );
}
