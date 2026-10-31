import { EmptyState } from "./EmptyState.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { Skeleton } from "./Skeleton.jsx";

function TreeNode({ node, onToggle }) {
  return (
    <li data-testid="scope-tree-node">
      <label className="flex items-center gap-2 py-1 text-text-primary">
        <input
          type="checkbox"
          checked={Boolean(node.checked)}
          onChange={() => onToggle?.(node)}
          aria-label={node.label}
        />
        <span>{node.label}</span>
        {typeof node.count === "number" ? (
          <span className="text-text-secondary">({node.count})</span>
        ) : null}
      </label>
      {node.children?.length ? (
        <ul className="ml-5 list-none">
          {node.children.map((child) => (
            <TreeNode key={child.id ?? child.label} node={child} onToggle={onToggle} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function ScopeTree({ state = "success", nodes = [], onToggle }) {
  if (state === "loading") {
    return (
      <div data-testid="scope-tree" data-state="loading">
        <Skeleton shape="row" count={5} />
      </div>
    );
  }
  if (state === "error") {
    return (
      <div data-testid="scope-tree" data-state="error">
        <ErrorBanner message="Failed to load scope" />
      </div>
    );
  }
  if (state === "empty") {
    return (
      <div data-testid="scope-tree" data-state="empty">
        <EmptyState message="Nothing discovered yet" />
      </div>
    );
  }

  return (
    <ul data-testid="scope-tree" data-state="success" role="tree" className="list-none font-ui">
      {nodes.map((node) => (
        <TreeNode key={node.id ?? node.label} node={node} onToggle={onToggle} />
      ))}
    </ul>
  );
}
