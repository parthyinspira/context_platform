import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/react";
import { AddSourceWizard } from "../src/components/AddSourceWizard.jsx";
import * as api from "../src/api.js";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const TREE = {
  roots: [
    {
      id: "root-1",
      kind: "repo",
      name: "billing-service",
      size_hint: 1000,
      children: [
        { id: "child-1", kind: "file", name: "billing-service/README.md", size_hint: 100, children: [] },
        { id: "child-2", kind: "file", name: "billing-service/main.py", size_hint: 900, children: [] },
      ],
    },
    {
      id: "root-2",
      kind: "repo",
      name: "other-repo",
      size_hint: 50,
      children: [],
    },
  ],
};

async function goToDiscoverStep() {
  fireEvent.click(screen.getByTestId("type-tile-git"));
  vi.spyOn(api, "testConnection").mockResolvedValue({ ok: true, error: null });
  fireEvent.click(screen.getByTestId("test-connection-button"));
  await screen.findByTestId("connect-success");
  vi.spyOn(api, "createSource").mockResolvedValue({ id: "src-1" });
  vi.spyOn(api, "discoverSource").mockResolvedValue(TREE);
  fireEvent.click(screen.getByTestId("add-source-submit"));
  await screen.findByTestId("scope-tree");
}

describe("AddSourceWizard discover step", () => {
  it("renders the discovered tree with sizes and counts nested under parents", async () => {
    render(<AddSourceWizard />);
    await goToDiscoverStep();

    const nodes = screen.getAllByTestId("scope-tree-node");
    expect(nodes).toHaveLength(4);
    expect(screen.getByText("billing-service")).toBeInTheDocument();
    expect(screen.getByText("(100)")).toBeInTheDocument();
  });

  it("toggling a parent checkbox checks all of its children", async () => {
    render(<AddSourceWizard />);
    await goToDiscoverStep();

    fireEvent.click(screen.getByLabelText("billing-service"));

    expect(screen.getByLabelText("billing-service/README.md")).toBeChecked();
    expect(screen.getByLabelText("billing-service/main.py")).toBeChecked();
  });

  it("filters the tree to matches and their ancestors when searching", async () => {
    render(<AddSourceWizard />);
    await goToDiscoverStep();

    fireEvent.change(screen.getByTestId("scope-search-input"), { target: { value: "readme" } });

    expect(screen.getByText("billing-service")).toBeInTheDocument();
    expect(screen.getByText("billing-service/README.md")).toBeInTheDocument();
    expect(screen.queryByText("billing-service/main.py")).not.toBeInTheDocument();
    expect(screen.queryByText("other-repo")).not.toBeInTheDocument();
  });

  it("select recommended checks every leaf node", async () => {
    render(<AddSourceWizard />);
    await goToDiscoverStep();

    fireEvent.click(screen.getByTestId("select-recommended-button"));

    expect(screen.getByLabelText("billing-service/README.md")).toBeChecked();
    expect(screen.getByLabelText("billing-service/main.py")).toBeChecked();
    expect(screen.getByLabelText("other-repo")).toBeChecked();
  });
});
