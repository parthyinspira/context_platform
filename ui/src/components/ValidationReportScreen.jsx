import { useEffect, useState } from "react";
import { Badge } from "./Badge.jsx";
import { Skeleton } from "./Skeleton.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { getRun, getRunValidation } from "../api.js";

const STATUS_VARIANT = { PASS: "success", WARN: "warning", FAIL: "danger" };

export function ValidationReportScreen({ runId, onBack }) {
  const [loadState, setLoadState] = useState("loading"); // loading | success | error
  const [run, setRun] = useState(null);
  const [report, setReport] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoadState("loading");
    Promise.all([getRun(runId), getRunValidation(runId)])
      .then(([runData, reportData]) => {
        if (cancelled) return;
        setRun(runData);
        setReport(reportData);
        setLoadState("success");
      })
      .catch(() => {
        if (cancelled) return;
        setLoadState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (loadState === "loading") {
    return (
      <div data-testid="validation-report">
        <Skeleton shape="block" count={3} />
      </div>
    );
  }
  if (loadState === "error") {
    return (
      <div data-testid="validation-report">
        <ErrorBanner message="Could not load the validation report" />
      </div>
    );
  }

  return (
    <div data-testid="validation-report">
      <button type="button" onClick={onBack}>
        Back
      </button>

      {report ? (
        <>
          <Badge variant={STATUS_VARIANT[report.status] ?? "info"} label={report.status} />

          {run.state === "QUARANTINED" && (
            <div data-testid="quarantine-explanation" role="status">
              This run was quarantined: previous knowledge remains published and this
              run's data was not applied.
            </div>
          )}

          <ul data-testid="validation-checks">
            {report.checks.map((check) => (
              <li key={check.name} data-testid={`check-${check.name}`}>
                <p>{check.name}</p>
                <p>{check.message}</p>
                <ul data-testid={`check-${check.name}-counts`}>
                  {Object.entries(check.counts ?? {}).map(([key, value]) => (
                    <li key={key}>
                      {key}: {value}
                    </li>
                  ))}
                </ul>
                {check.samples?.length ? (
                  <ul data-testid={`check-${check.name}-samples`}>
                    {check.samples.map((sample) => (
                      <li key={sample}>{sample}</li>
                    ))}
                  </ul>
                ) : (
                  <p data-testid={`check-${check.name}-samples-none`}>none</p>
                )}
              </li>
            ))}
          </ul>
        </>
      ) : (
        <div data-testid="validation-report-fallback">
          <p>No validation report is available for this run yet.</p>
          <p data-testid="fallback-state">State: {run.state}</p>
          {run.error && <p data-testid="fallback-error">{run.error}</p>}
        </div>
      )}
    </div>
  );
}
