export function EmptyState({ message, actionLabel, onAction }) {
  return (
    <div
      data-testid="empty-state"
      role="status"
      className="flex flex-col items-center gap-3 rounded-card border border-dashed border-border-subtle bg-bg-canvas px-6 py-8 text-center font-ui"
    >
      <p className="text-text-secondary">{message}</p>
      {actionLabel ? (
        <button
          type="button"
          onClick={onAction}
          className="rounded-control border border-border-subtle px-3 py-1 text-text-primary hover:bg-bg-surface"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
