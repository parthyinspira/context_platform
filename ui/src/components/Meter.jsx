import { EmptyState } from "./EmptyState.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { Skeleton } from "./Skeleton.jsx";

export function Meter({ state = "success", label, value = 0, max = 100 }) {
  if (state === "loading") {
    return (
      <div data-testid="meter" data-state="loading">
        <Skeleton shape="block" count={1} />
      </div>
    );
  }
  if (state === "error") {
    return (
      <div data-testid="meter" data-state="error">
        <ErrorBanner message="Failed to load budget" />
      </div>
    );
  }
  if (state === "empty") {
    return (
      <div data-testid="meter" data-state="empty">
        <EmptyState message="No budget set" />
      </div>
    );
  }

  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
  return (
    <div data-testid="meter" data-state="success" className="flex flex-col gap-1 font-ui">
      <div className="flex justify-between text-text-secondary">
        <span>{label}</span>
        <span>
          {value} / {max}
        </span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        className="h-2 w-full overflow-hidden rounded-control bg-bg-canvas"
      >
        <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
