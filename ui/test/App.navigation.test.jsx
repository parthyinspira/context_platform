import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/react";
import { App } from "../src/App.jsx";
import * as api from "../src/api.js";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const SOURCE = {
  id: "11111111-1111-1111-1111-111111111111",
  type: "git",
  uri: "https://github.com/example/repo",
  schedule: "0 * * * *",
  credentials_ref: "ref",
  owner: "team",
  sensitivity: "internal",
  status: "active",
};

describe("App navigation", () => {
  it("navigates to the Sources screen and then to the run view after Run", async () => {
    vi.spyOn(api, "listSources").mockResolvedValue([SOURCE]);
    vi.spyOn(api, "runSource").mockResolvedValue({
      id: "run-1",
      source_id: SOURCE.id,
      status: "queued",
    });
    vi.spyOn(api, "getRun").mockResolvedValue({
      id: "run-1",
      source_id: SOURCE.id,
      state: "APPROVED",
      plan: { include: [], exclude: [], size_cap_bytes: null, budgets: {} },
      manifest_summary: { discovered: 0, fetched: 0, skipped: 0, failed: 0, fetched_bytes: 0 },
      log_entries: [],
      error: null,
    });

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Sources" }));
    await screen.findByTestId("sources-table");

    fireEvent.click(await screen.findByRole("button", { name: "Run" }));

    expect(await screen.findByTestId("run-id")).toHaveTextContent("run-1");
  });

  it("navigates from a published run to its validation report and back", async () => {
    vi.spyOn(api, "listSources").mockResolvedValue([SOURCE]);
    vi.spyOn(api, "runSource").mockResolvedValue({ id: "run-1", source_id: SOURCE.id, status: "queued" });
    vi.spyOn(api, "getRun").mockResolvedValue({
      id: "run-1",
      source_id: SOURCE.id,
      state: "PUBLISHED",
      plan: { include: [], exclude: [], size_cap_bytes: null, budgets: {} },
      manifest_summary: { discovered: 0, fetched: 0, skipped: 0, failed: 0, fetched_bytes: 0 },
      log_entries: [],
      error: null,
    });
    vi.spyOn(api, "getRunValidation").mockResolvedValue({ status: "PASS", checks: [] });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Sources" }));
    await screen.findByTestId("sources-table");
    fireEvent.click(await screen.findByRole("button", { name: "Run" }));
    await screen.findByTestId("run-id");

    fireEvent.click(screen.getByTestId("view-validation-report-link"));
    await screen.findByTestId("validation-report");

    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(await screen.findByTestId("run-id")).toBeInTheDocument();
  });
});
