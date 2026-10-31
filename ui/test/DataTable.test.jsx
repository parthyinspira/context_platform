import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { DataTable } from "../src/components/DataTable.jsx";

afterEach(cleanup);

const columns = [
  { key: "name", label: "Name" },
  { key: "type", label: "Type" },
];
const rows = [
  { id: "1", name: "repo-a", type: "git" },
  { id: "2", name: "repo-b", type: "git" },
];

describe("DataTable", () => {
  it("renders a header per column and a row per data row", () => {
    render(<DataTable state="success" columns={columns} rows={rows} />);
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getAllByTestId("data-table-row")).toHaveLength(2);
  });

  it("shows skeleton rows in the loading state", () => {
    render(<DataTable state="loading" columns={columns} />);
    expect(screen.getByTestId("data-table")).toHaveAttribute("data-state", "loading");
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("shows an error banner in the error state", () => {
    render(<DataTable state="error" columns={columns} errorMessage="Could not load sources" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Could not load sources");
  });

  it("shows an empty state with no rows", () => {
    render(<DataTable state="empty" columns={columns} emptyMessage="Add a source" />);
    expect(screen.getByTestId("empty-state")).toHaveTextContent("Add a source");
  });
});
