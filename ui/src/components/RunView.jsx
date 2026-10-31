export function RunView({ run }) {
  return (
    <div data-testid="run-view">
      <p>
        Run <span data-testid="run-id">{run.id}</span>
      </p>
      <p>
        Source <span data-testid="run-source-id">{run.source_id}</span>
      </p>
      <p>
        Status <span data-testid="run-status">{run.status}</span>
      </p>
    </div>
  );
}
