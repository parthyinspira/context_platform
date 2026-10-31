import { EmptyState } from "./EmptyState.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { Skeleton } from "./Skeleton.jsx";

export function Stepper({ state = "success", steps = [], activeStep = 0 }) {
  if (state === "loading") {
    return (
      <div data-testid="stepper" data-state="loading">
        <Skeleton shape="row" count={steps.length || 3} />
      </div>
    );
  }
  if (state === "error") {
    return (
      <div data-testid="stepper" data-state="error">
        <ErrorBanner message="Failed to load steps" />
      </div>
    );
  }
  if (state === "empty") {
    return (
      <div data-testid="stepper" data-state="empty">
        <EmptyState message="No steps configured" />
      </div>
    );
  }

  return (
    <ol data-testid="stepper" data-state="success" className="flex list-none gap-4 font-ui">
      {steps.map((step, index) => {
        const status = index < activeStep ? "complete" : index === activeStep ? "current" : "pending";
        return (
          <li
            key={step.id ?? step.label}
            data-testid="stepper-step"
            data-status={status}
            aria-current={status === "current" ? "step" : undefined}
            className={
              status === "current"
                ? "font-semibold text-accent"
                : status === "complete"
                  ? "text-success"
                  : "text-text-secondary"
            }
          >
            <span aria-hidden="true">{status === "complete" ? "✓" : index + 1}</span> {step.label}
          </li>
        );
      })}
    </ol>
  );
}
