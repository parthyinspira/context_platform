import { useEffect, useState } from "react";
import { listSources, runSource } from "../api.js";

export function SourcesScreen({ onRunStarted }) {
  const [state, setState] = useState("loading");
  const [sources, setSources] = useState([]);
  const [lastRunBySourceId, setLastRunBySourceId] = useState({});
  const [runError, setRunError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    listSources()
      .then((rows) => {
        if (cancelled) return;
        setSources(rows);
        setState(rows.length === 0 ? "empty" : "success");
      })
      .catch(() => {
        if (cancelled) return;
        setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleRun(sourceId) {
    setRunError(null);
    try {
      const run = await runSource(sourceId);
      setLastRunBySourceId((prev) => ({ ...prev, [sourceId]: run.status }));
      onRunStarted(run);
    } catch {
      setRunError(`Could not start a run for source ${sourceId}`);
    }
  }

  if (state === "loading") {
    return <p data-testid="sources-loading">Loading sources…</p>;
  }

  if (state === "error") {
    return (
      <p data-testid="sources-error" role="alert">
        Could not load sources.
      </p>
    );
  }

  if (state === "empty") {
    return (
      <div data-testid="sources-empty">
        <p>No sources yet.</p>
        <p>Register a source to start harvesting.</p>
      </div>
    );
  }

  return (
    <div>
      {runError && (
        <p data-testid="run-error" role="alert">
          {runError}
        </p>
      )}
      <table data-testid="sources-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Status</th>
            <th>Last run</th>
            <th>Validation</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((source) => (
            <tr key={source.id} data-testid={`source-row-${source.id}`}>
              <td>{source.uri}</td>
              <td>{source.type}</td>
              <td>{source.status}</td>
              <td data-testid={`last-run-${source.id}`}>
                {lastRunBySourceId[source.id] ?? "Never"}
              </td>
              <td>
                <span data-testid={`validation-badge-${source.id}`}>Not yet validated</span>
              </td>
              <td>
                {source.status === "active" && (
                  <button type="button" onClick={() => handleRun(source.id)}>
                    Run
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
