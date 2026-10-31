import { EmptyState } from "./EmptyState.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { Skeleton } from "./Skeleton.jsx";

export function DataTable({ state = "success", columns = [], rows = [], emptyMessage = "No rows yet", errorMessage = "Failed to load table" }) {
  if (state === "loading") {
    return (
      <div data-testid="data-table" data-state="loading">
        <Skeleton shape="row" count={4} />
      </div>
    );
  }
  if (state === "error") {
    return (
      <div data-testid="data-table" data-state="error">
        <ErrorBanner message={errorMessage} />
      </div>
    );
  }
  if (state === "empty") {
    return (
      <div data-testid="data-table" data-state="empty">
        <EmptyState message={emptyMessage} />
      </div>
    );
  }

  return (
    <table data-testid="data-table" data-state="success" className="w-full border-collapse font-ui">
      <thead>
        <tr>
          {columns.map((col) => (
            <th
              key={col.key}
              className="border-b border-border-subtle px-3 py-2 text-left text-text-secondary"
            >
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id} data-testid="data-table-row">
            {columns.map((col) => (
              <td key={col.key} className="border-b border-border-subtle px-3 py-2 text-text-primary">
                {row[col.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
