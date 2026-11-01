import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import * as api from "../src/api.js";

vi.mock("../src/components/GraphCanvas.jsx", () => ({
  GraphCanvas: ({ nodes, edges }) => (
    <div data-testid="graph-canvas">{`${nodes.length} nodes, ${edges.length} edges`}</div>
  ),
}));

import { GraphScreen } from "../src/components/GraphScreen.jsx";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const GRAPH = {
  nodes: [
    { id: "repo-1", label: "billing-service", type: "Repository" },
    { id: "svc-1", label: "billing", type: "Service" },
  ],
  edges: [{ id: "e1", source: "repo-1", target: "svc-1", relation: "CONTAINS" }],
};

describe("GraphScreen", () => {
  it("shows a loading state before the graph resolves", async () => {
    vi.spyOn(api, "getGraph").mockReturnValue(new Promise(() => {}));
    render(<GraphScreen />);
    expect(screen.getByTestId("graph-loading")).toBeInTheDocument();
  });

  it("renders the GraphCanvas once the graph loads", async () => {
    vi.spyOn(api, "getGraph").mockResolvedValue(GRAPH);
    render(<GraphScreen />);
    expect(await screen.findByTestId("graph-canvas")).toHaveTextContent("2 nodes, 1 edges");
  });

  it("shows an empty state when there are no nodes", async () => {
    vi.spyOn(api, "getGraph").mockResolvedValue({ nodes: [], edges: [] });
    render(<GraphScreen />);
    expect(await screen.findByTestId("empty-state")).toBeInTheDocument();
  });

  it("shows an error state when the graph fails to load", async () => {
    vi.spyOn(api, "getGraph").mockRejectedValue(new Error("boom"));
    render(<GraphScreen />);
    expect(await screen.findByTestId("error-banner")).toBeInTheDocument();
  });
});
