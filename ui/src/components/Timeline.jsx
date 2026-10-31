import { EmptyState } from "./EmptyState.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { Skeleton } from "./Skeleton.jsx";

const STATUS_ICON = {
  pending: "○",
  active: "●",
  done: "✓",
  failed: "✕",
};

const STATUS_CLASS = {
  pending: "text-text-secondary",
  active: "text-accent",
  done: "text-success",
  failed: "text-danger",
};

export function Timeline({ state = "success", stages = [] }) {
  if (state === "loading") {
    return (
      <div data-testid="timeline" data-state="loading">
        <Skeleton shape="row" count={stages.length || 4} />
      </div>
    );
  }
  if (state === "error") {
    return (
      <div data-testid="timeline" data-state="error">
        <ErrorBanner message="Failed to load run" />
      </div>
    );
  }
  if (state === "empty") {
    return (
      <div data-testid="timeline" data-state="empty">
        <EmptyState message="No run started" />
      </div>
    );
  }

  return (
    <ol data-testid="timeline" data-state="success" className="flex list-none gap-4 font-ui">
      {stages.map((stage) => (
        <li
          key={stage.id ?? stage.name}
          data-testid="timeline-stage"
          data-status={stage.status}
          className={STATUS_CLASS[stage.status] ?? STATUS_CLASS.pending}
        >
          <span aria-hidden="true">{STATUS_ICON[stage.status] ?? STATUS_ICON.pending}</span>{" "}
          <span>{stage.name}</span>
          <span className="sr-only"> ({stage.status})</span>
        </li>
      ))}
    </ol>
  );
}
