import { Skeleton } from "./Skeleton.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";

// Minimal mapping onto what POST /sources/{id}/plan actually returns (no generic
// pulled-vs-skipped byte split exists in `Profile`): counts_by_type stands in for
// "pulled by type", and the plan's include/exclude patterns stand in for what
// will be pulled vs. skipped by rule.
export function PlanSummaryCard({
  state = "success",
  profile,
  plan,
  estimatedBytes,
  estimatedFiles,
  estimatedSeconds,
  estimatedTokens,
  budgetWarnings = [],
}) {
  if (state === "loading") {
    return (
      <div data-testid="plan-summary-card" data-state="loading">
        <Skeleton shape="block" count={1} />
      </div>
    );
  }
  if (state === "error") {
    return (
      <div data-testid="plan-summary-card" data-state="error">
        <ErrorBanner message="Failed to load plan preview" />
      </div>
    );
  }

  return (
    <div data-testid="plan-summary-card" data-state="success">
      <h3>What will be pulled (by type)</h3>
      <ul data-testid="plan-counts-by-type">
        {Object.entries(profile?.counts_by_type ?? {}).map(([type, count]) => (
          <li key={type} data-testid={`plan-type-${type}`}>
            {type}: {count}
          </li>
        ))}
      </ul>

      <p data-testid="plan-include">Include: {(plan?.include ?? []).join(", ") || "(everything)"}</p>
      <p data-testid="plan-exclude">Skipped (exclude): {(plan?.exclude ?? []).join(", ") || "(none)"}</p>

      <dl data-testid="plan-estimates">
        <dt>Bytes</dt>
        <dd data-testid="estimate-bytes">{estimatedBytes}</dd>
        <dt>Files</dt>
        <dd data-testid="estimate-files">{estimatedFiles}</dd>
        <dt>Time (s)</dt>
        <dd data-testid="estimate-seconds">{estimatedSeconds}</dd>
        <dt>Tokens</dt>
        <dd data-testid="estimate-tokens">{estimatedTokens}</dd>
      </dl>

      {budgetWarnings.length > 0 && (
        <ul data-testid="budget-warnings">
          {budgetWarnings.map((warning) => (
            <li key={warning} data-testid="budget-warning" role="alert">
              ⚠ {warning}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
