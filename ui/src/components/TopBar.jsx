export function TopBar({ theme, onToggleTheme }) {
  return (
    <header
      data-testid="top-bar"
      className="flex items-center gap-4 border-b border-border-subtle bg-bg-surface px-4 py-2 font-ui"
    >
      <input
        type="search"
        placeholder="Search (/)"
        aria-label="Global search"
        className="max-w-[480px] flex-1 rounded-control border border-border-subtle bg-bg-canvas px-3 py-1 text-text-primary"
      />
      <span className="rounded-control bg-bg-canvas px-2 py-1 text-xs text-text-secondary">
        local
      </span>
      <button
        type="button"
        data-testid="theme-toggle"
        aria-label="Toggle light and dark theme"
        onClick={onToggleTheme}
        className="rounded-control border border-border-subtle px-3 py-1 text-text-primary hover:bg-bg-canvas"
      >
        {theme === "dark" ? "Dark" : "Light"}
      </button>
      <span className="text-text-secondary">User</span>
    </header>
  );
}
