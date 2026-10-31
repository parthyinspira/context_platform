export function TopBar({ theme, onToggleTheme }) {
  return (
    <header data-testid="top-bar" className="top-bar">
      <input
        type="search"
        placeholder="Search (/)"
        aria-label="Global search"
        className="top-bar-search"
      />
      <span className="env-badge">local</span>
      <button
        type="button"
        data-testid="theme-toggle"
        aria-label="Toggle light and dark theme"
        onClick={onToggleTheme}
      >
        {theme === "dark" ? "Dark" : "Light"}
      </button>
      <span className="user-badge">User</span>
    </header>
  );
}
