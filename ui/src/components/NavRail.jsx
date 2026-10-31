const NAV_ITEMS = ["Graph", "Sources", "Runs", "Agents", "Settings"];

export function NavRail({ active = "Graph" }) {
  return (
    <nav data-testid="nav-rail" className="nav-rail">
      <ul>
        {NAV_ITEMS.map((item) => (
          <li key={item} aria-current={item === active ? "page" : undefined}>
            {item}
          </li>
        ))}
      </ul>
    </nav>
  );
}
