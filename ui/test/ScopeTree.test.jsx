import { describe, it, expect, afterEach, vi } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { ScopeTree } from "../src/components/ScopeTree.jsx";

afterEach(cleanup);

const nodes = [
  {
    id: "repo",
    label: "repo-a",
    count: 42,
    checked: true,
    children: [{ id: "src", label: "src/", count: 10, checked: false }],
  },
];

describe("ScopeTree", () => {
  it("renders nested nodes with label, count and checkbox state", () => {
    render(<ScopeTree state="success" nodes={nodes} />);
    const rows = screen.getAllByTestId("scope-tree-node");
    expect(rows).toHaveLength(2);
    expect(screen.getByLabelText("repo-a")).toBeChecked();
    expect(screen.getByLabelText("src/")).not.toBeChecked();
    expect(screen.getByText("(42)")).toBeInTheDocument();
  });

  it("calls onToggle when a node checkbox changes", () => {
    const onToggle = vi.fn();
    render(<ScopeTree state="success" nodes={nodes} onToggle={onToggle} />);
    fireEvent.click(screen.getByLabelText("repo-a"));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it("shows skeleton rows in the loading state", () => {
    render(<ScopeTree state="loading" />);
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("shows an error banner in the error state", () => {
    render(<ScopeTree state="error" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows an empty state with nothing discovered", () => {
    render(<ScopeTree state="empty" />);
    expect(screen.getByTestId("empty-state")).toHaveTextContent("Nothing discovered yet");
  });
});
