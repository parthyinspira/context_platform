import { useEffect, useState } from "react";
import { Timeline } from "./Timeline.jsx";
import { Meter } from "./Meter.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { getRun, stopRun } from "../api.js";

const POLL_INTERVAL_MS = 2000;

const TERMINAL_STATES = ["PUBLISHED", "QUARANTINED", "FAILED", "PARTIAL"];
const TERMINAL_FAILURE_STATES = ["QUARANTINED", "FAILED", "PARTIAL"];
const REPORT_STATES = ["PUBLISHED", "QUARANTINED", "PARTIAL"];

// `harvesters/run.py` only ever persists APPROVED -> HARVESTING -> VALIDATING ->
// a terminal state today (no CONNECTING/DISCOVERING/PROFILING/PLANNED rows are
// written), but the full lifecycle order is kept here so the timeline is correct
// once a harvester starts reporting those intermediate states too.
const STAGE_ORDER = [
  "CONNECTING",
  "DISCOVERING",
  "PROFILING",
  "PLANNED",
  "APPROVED",
  "HARVESTING",
  "VALIDATING",
  "PUBLISHED",
];

function buildStages(state) {
  if (TERMINAL_FAILURE_STATES.includes(state)) {
    return [
      ...STAGE_ORDER.slice(0, -1).map((name) => ({ name, status: "done" })),
      { name: state, status: "failed" },
    ];
  }
  const idx = STAGE_ORDER.indexOf(state);
  const effectiveIdx = idx === -1 ? 0 : idx;
  return STAGE_ORDER.map((name, i) => ({
    name,
    status: i < effectiveIdx ? "done" : i === effectiveIdx ? "active" : "pending",
  }));
}

function meterProps(budgetValue, value) {
  return budgetValue == null
    ? { state: "empty" }
    : { state: "success", value, max: budgetValue };
}

export function RunView({ run, onViewValidationReport, onBackToSources }) {
  const [detail, setDetail] = useState(null);
  const [loadError, setLoadError] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [stopError, setStopError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    let timer;

    function poll() {
      getRun(run.id)
        .then((data) => {
          if (cancelled) return;
          setDetail(data);
          setLoadError(false);
          if (!TERMINAL_STATES.includes(data.state)) {
            timer = setTimeout(poll, POLL_INTERVAL_MS);
          }
        })
        .catch(() => {
          if (cancelled) return;
          setLoadError(true);
        });
    }

    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [run.id]);

  async function handleStop() {
    setStopping(true);
    setStopError(null);
    try {
      const updated = await stopRun(run.id);
      setDetail(updated);
    } catch {
      setStopError("Could not stop the run");
    } finally {
      setStopping(false);
    }
  }

  if (!detail) {
    return (
      <div data-testid="run-view">
        {loadError ? <ErrorBanner message="Could not load run status" /> : <Timeline state="loading" />}
      </div>
    );
  }

  const isTerminal = TERMINAL_STATES.includes(detail.state);
  const budgets = detail.plan?.budgets ?? {};
  const manifest = detail.manifest_summary;

  return (
    <div data-testid="run-view">
      <p>
        Run <span data-testid="run-id">{detail.id}</span>
      </p>
      <p>
        Source <span data-testid="run-source-id">{detail.source_id}</span>
      </p>
      <p>
        Status <span data-testid="run-status">{detail.state}</span>
      </p>

      <Timeline state="success" stages={buildStages(detail.state)} />

      <ul data-testid="run-log">
        {detail.log_entries.map((entry) => (
          <li key={entry.ref} data-testid="run-log-line">
            {entry.ref} — {entry.outcome ?? "discovered"}
            {entry.outcome_reason ? ` (${entry.outcome_reason})` : ""}
          </li>
        ))}
      </ul>

      <Meter label="Files" {...meterProps(budgets.max_files, manifest.fetched)} />
      <Meter label="Bytes" {...meterProps(budgets.max_bytes, manifest.fetched_bytes)} />
      <Meter label="Time (s)" {...meterProps(budgets.max_seconds, 0)} />
      <Meter label="Tokens" {...meterProps(budgets.max_tokens, 0)} />

      {!isTerminal && (
        <>
          <button type="button" data-testid="stop-run-button" disabled={stopping} onClick={handleStop}>
            Stop
          </button>
          {stopError && <ErrorBanner message={stopError} />}
        </>
      )}

      {isTerminal && (
        <div data-testid="run-next-steps">
          {REPORT_STATES.includes(detail.state) ? (
            <button
              type="button"
              data-testid="view-validation-report-link"
              onClick={() => onViewValidationReport?.(detail.id)}
            >
              View validation report
            </button>
          ) : (
            <button type="button" data-testid="back-to-sources-link" onClick={onBackToSources}>
              Back to sources
            </button>
          )}
        </div>
      )}
    </div>
  );
}
