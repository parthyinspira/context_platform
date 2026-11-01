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
    { id: "leaf-1", kind: "file", name: "a.sql", size_hint: 10, children: [] },
    { id: "leaf-2", kind: "file", name: "b.py", size_hint: 20, children: [] },
  ],
};

const PLAN_RESPONSE = {
  plan: { include: ["*.sql"], exclude: ["*.py"], size_cap_bytes: 1000, budgets: {} },
  profile: { object_count: 2, total_bytes: 30, detected_stacks: ["sql"], counts_by_type: { sql: 1, py: 1 } },
  estimated_bytes: 30,
  estimated_files: 2,
  estimated_seconds: 1,
  estimated_tokens: 7,
  budget_warnings: [],
};

async function goToPlanStep(planResponse = PLAN_RESPONSE) {
  fireEvent.click(screen.getByTestId("type-tile-git"));
  vi.spyOn(api, "testConnection").mockResolvedValue({ ok: true, error: null });
  fireEvent.click(screen.getByTestId("test-connection-button"));
  await screen.findByTestId("connect-success");
  vi.spyOn(api, "createSource").mockResolvedValue({ id: "src-1" });
  vi.spyOn(api, "discoverSource").mockResolvedValue(TREE);
  fireEvent.click(screen.getByTestId("add-source-submit"));
  await screen.findByTestId("scope-tree");

  fireEvent.click(screen.getByTestId("select-recommended-button"));
  vi.spyOn(api, "planSource").mockResolvedValue(planResponse);
  fireEvent.click(screen.getByTestId("discover-next-button"));
  await screen.findByTestId("plan-summary-card");
}

describe("AddSourceWizard plan & run step", () => {
  it("shows pulled/skipped groups, estimates and no warnings when none apply", async () => {
    render(<AddSourceWizard />);
    await goToPlanStep();

    expect(screen.getByTestId("plan-type-sql")).toHaveTextContent("sql: 1");
    expect(screen.getByTestId("estimate-bytes")).toHaveTextContent("30");
    expect(screen.getByTestId("estimate-tokens")).toHaveTextContent("7");
    expect(screen.queryByTestId("budget-warnings")).not.toBeInTheDocument();
  });

  it("shows a budget warning when the plan response includes one", async () => {
    render(<AddSourceWizard />);
    await goToPlanStep({ ...PLAN_RESPONSE, budget_warnings: ["estimated bytes (30) exceed budget max_bytes (10)"] });

    expect(screen.getByTestId("budget-warning")).toHaveTextContent("max_bytes");
  });

  it("sends edited include/exclude patterns when starting the run", async () => {
    render(<AddSourceWizard />);
    await goToPlanStep();

    fireEvent.change(screen.getByTestId("plan-exclude-input"), {
      target: { value: "*.py, *.log" },
    });

    const createRun = vi.spyOn(api, "createRun").mockResolvedValue({ id: "run-1", source_id: "src-1", state: "APPROVED" });
    fireEvent.click(screen.getByTestId("run-now-button"));

    await waitFor(() =>
      expect(createRun).toHaveBeenCalledWith(
        "src-1",
        expect.objectContaining({ exclude: ["*.py", "*.log"] })
      )
    );
  });

  it("shows an error and stays on the step when Run now fails", async () => {
    render(<AddSourceWizard />);
    await goToPlanStep();

    vi.spyOn(api, "createRun").mockRejectedValue(new Error("boom"));
    fireEvent.click(screen.getByTestId("run-now-button"));

    expect(await screen.findByTestId("error-banner")).toBeInTheDocument();
    expect(screen.getByTestId("wizard-step-plan")).toBeInTheDocument();
  });

  it("navigates to the run view on successful Run now", async () => {
    const onRunStarted = vi.fn();
    render(<AddSourceWizard onRunStarted={onRunStarted} />);
    await goToPlanStep();

    const run = { id: "run-1", source_id: "src-1", state: "APPROVED" };
    vi.spyOn(api, "createRun").mockResolvedValue(run);
    fireEvent.click(screen.getByTestId("run-now-button"));

    await waitFor(() => expect(onRunStarted).toHaveBeenCalledWith(run));
  });
});
