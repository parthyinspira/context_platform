import { EmptyState } from "./EmptyState.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { Skeleton } from "./Skeleton.jsx";

const VARIANTS = {
  success: { colorClass: "bg-success text-bg-surface", icon: "✓" },
  warning: { colorClass: "bg-warning text-bg-surface", icon: "!" },
  danger: { colorClass: "bg-danger text-bg-surface", icon: "✕" },
  info: { colorClass: "bg-accent text-bg-surface", icon: "i" },
};

export function Badge({ state = "success", variant = "info", label }) {
  if (state === "loading") {
    return (
      <div data-testid="badge" data-state="loading">
        <Skeleton shape="row" count={1} />
      </div>
    );
  }
  if (state === "error") {
    return (
      <div data-testid="badge" data-state="error">
        <ErrorBanner message="Status unavailable" />
      </div>
    );
  }
  if (state === "empty") {
    return (
      <div data-testid="badge" data-state="empty">
        <EmptyState message="No status" />
      </div>
    );
  }

  const { colorClass, icon } = VARIANTS[variant] ?? VARIANTS.info;
  return (
    <span
      data-testid="badge"
      data-state="success"
      data-variant={variant}
      className={`inline-flex items-center gap-1 rounded-control px-2 py-0.5 text-xs font-ui ${colorClass}`}
    >
      <span aria-hidden="true">{icon}</span>
      <span>{label}</span>
    </span>
  );
}
