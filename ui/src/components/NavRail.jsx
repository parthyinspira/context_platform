const NAV_ITEMS = ["Graph", "Sources", "Runs", "Agents", "Settings"];

export function NavRail({ active = "Graph" }) {
  return (
    <nav
      data-testid="nav-rail"
      className="flex w-[220px] shrink-0 flex-col bg-bg-surface border-r border-border-subtle font-ui"
    >
      <ul className="m-0 list-none py-4">
        {NAV_ITEMS.map((item) => (
          <li
            key={item}
            aria-current={item === active ? "page" : undefined}
            className="px-4 py-2 text-text-secondary aria-[current=page]:text-accent aria-[current=page]:font-semibold"
          >
            {item}
          </li>
        ))}
      </ul>
    </nav>
  );
}
