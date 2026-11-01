import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { ValidationReportScreen } from "../src/components/ValidationReportScreen.jsx";
import * as api from "../src/api.js";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function run(overrides = {}) {
  return { id: "run-1", source_id: "src-1", state: "PUBLISHED", error: null, ...overrides };
}

describe("ValidationReportScreen", () => {
  it("shows the overall status badge for the report", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(run());
    vi.spyOn(api, "getRunValidation").mockResolvedValue({ status: "FAIL", checks: [] });

    render(<ValidationReportScreen runId="run-1" />);

    const badge = await screen.findByTestId("badge");
    expect(badge).toHaveAttribute("data-variant", "danger");
    expect(badge).toHaveTextContent("FAIL");
  });

  it("lists every check with its counts and samples, showing 'none' when empty", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(run());
    vi.spyOn(api, "getRunValidation").mockResolvedValue({
      status: "WARN",
      checks: [
        { name: "completeness", status: "WARN", message: "ok-ish", counts: { fetched: 9 }, samples: ["a.txt"] },
        { name: "budget_compliance", status: "PASS", message: "fine", counts: {}, samples: [] },
      ],
    });

    render(<ValidationReportScreen runId="run-1" />);

    await screen.findByTestId("check-completeness");
    expect(screen.getByTestId("check-completeness-counts")).toHaveTextContent("fetched: 9");
    expect(screen.getByTestId("check-completeness-samples")).toHaveTextContent("a.txt");
    expect(screen.getByTestId("check-budget_compliance-samples-none")).toHaveTextContent("none");
  });

  it("shows the quarantine explanation only when the run is quarantined", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(run({ state: "QUARANTINED" }));
    vi.spyOn(api, "getRunValidation").mockResolvedValue({ status: "FAIL", checks: [] });

    render(<ValidationReportScreen runId="run-1" />);

    expect(await screen.findByTestId("quarantine-explanation")).toBeInTheDocument();
  });

  it("does not show the quarantine explanation for a published run", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(run({ state: "PUBLISHED" }));
    vi.spyOn(api, "getRunValidation").mockResolvedValue({ status: "PASS", checks: [] });

    render(<ValidationReportScreen runId="run-1" />);

    await screen.findByTestId("badge");
    expect(screen.queryByTestId("quarantine-explanation")).not.toBeInTheDocument();
  });

  it("shows a fallback with the run's state and error when no report exists yet", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(run({ state: "FAILED", error: "connect failed: timeout" }));
    vi.spyOn(api, "getRunValidation").mockResolvedValue(null);

    render(<ValidationReportScreen runId="run-1" />);

    expect(await screen.findByTestId("validation-report-fallback")).toBeInTheDocument();
    expect(screen.getByTestId("fallback-state")).toHaveTextContent("FAILED");
    expect(screen.getByTestId("fallback-error")).toHaveTextContent("connect failed: timeout");
  });
});
