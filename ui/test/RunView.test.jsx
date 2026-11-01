import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/react";
import { RunView } from "../src/components/RunView.jsx";
import * as api from "../src/api.js";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const RUN = { id: "run-1", source_id: "src-1" };

function detail(overrides = {}) {
  return {
    id: "run-1",
    source_id: "src-1",
    state: "HARVESTING",
    plan: { include: [], exclude: [], size_cap_bytes: null, budgets: { max_files: 10, max_bytes: null, max_seconds: null, max_tokens: null } },
    manifest_summary: { discovered: 5, fetched: 3, skipped: 1, failed: 0, fetched_bytes: 300 },
    log_entries: [
      { ref: "a.py", outcome: "fetched", outcome_reason: "ok" },
      { ref: "b.py", outcome: "skipped", outcome_reason: "excluded" },
    ],
    error: null,
    ...overrides,
  };
}

describe("RunView", () => {
  it("shows the live stage as active with manifest counts", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(detail({ state: "HARVESTING" }));
    render(<RunView run={RUN} />);

    await screen.findByTestId("timeline");
    const harvestingStage = screen
      .getAllByTestId("timeline-stage")
      .find((el) => el.textContent.includes("HARVESTING"));
    expect(harvestingStage).toHaveAttribute("data-status", "active");
  });

  it("marks the run done once it reaches a terminal state and stops polling", async () => {
    const getRun = vi.spyOn(api, "getRun").mockResolvedValue(detail({ state: "PUBLISHED" }));
    render(<RunView run={RUN} />);

    expect(await screen.findByTestId("run-status")).toHaveTextContent("PUBLISHED");
    await new Promise((r) => setTimeout(r, 0));
    expect(getRun).toHaveBeenCalledTimes(1);
  });

  it("renders one log line per manifest entry in order", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(detail());
    render(<RunView run={RUN} />);

    const lines = await screen.findAllByTestId("run-log-line");
    expect(lines).toHaveLength(2);
    expect(lines[0]).toHaveTextContent("a.py");
    expect(lines[1]).toHaveTextContent("b.py");
  });

  it("shows a files meter with value/max and an empty tokens meter when unset", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(detail());
    render(<RunView run={RUN} />);

    await screen.findByTestId("run-view");
    const meters = screen.getAllByTestId("meter");
    expect(meters[0]).toHaveAttribute("data-state", "success");
    expect(meters[0]).toHaveTextContent("3 / 10");
    const tokensMeter = meters[3];
    expect(tokensMeter).toHaveAttribute("data-state", "empty");
  });

  it("shows Stop while non-terminal and hides it once the run is terminal", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(detail({ state: "HARVESTING" }));
    render(<RunView run={RUN} />);
    expect(await screen.findByTestId("stop-run-button")).toBeInTheDocument();
    cleanup();

    vi.spyOn(api, "getRun").mockResolvedValue(detail({ state: "PUBLISHED" }));
    render(<RunView run={RUN} />);
    await screen.findByTestId("run-status");
    expect(screen.queryByTestId("stop-run-button")).not.toBeInTheDocument();
  });

  it("calling Stop shows the resulting failed state", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(detail({ state: "HARVESTING" }));
    vi.spyOn(api, "stopRun").mockResolvedValue(detail({ state: "FAILED", error: "stopped by user" }));
    render(<RunView run={RUN} />);

    fireEvent.click(await screen.findByTestId("stop-run-button"));

    await waitFor(() => expect(screen.getByTestId("run-status")).toHaveTextContent("FAILED"));
  });

  it("shows a report link when published and a back-to-sources link when failed", async () => {
    vi.spyOn(api, "getRun").mockResolvedValue(detail({ state: "PUBLISHED" }));
    render(<RunView run={RUN} />);
    expect(await screen.findByTestId("view-validation-report-link")).toBeInTheDocument();
    cleanup();

    vi.spyOn(api, "getRun").mockResolvedValue(detail({ state: "FAILED", error: "connect failed" }));
    render(<RunView run={RUN} />);
    expect(await screen.findByTestId("back-to-sources-link")).toBeInTheDocument();
  });
});
