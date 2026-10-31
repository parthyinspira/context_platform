import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/react";
import { SourcesScreen } from "../src/components/SourcesScreen.jsx";
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

describe("SourcesScreen", () => {
  it("shows a loading state before sources resolve", () => {
    vi.spyOn(api, "listSources").mockReturnValue(new Promise(() => {}));
    render(<SourcesScreen onRunStarted={() => {}} />);
    expect(screen.getByTestId("sources-loading")).toBeInTheDocument();
  });

  it("renders sources with status, last run and validation badge", async () => {
    vi.spyOn(api, "listSources").mockResolvedValue([SOURCE]);
    render(<SourcesScreen onRunStarted={() => {}} />);

    const row = await screen.findByTestId(`source-row-${SOURCE.id}`);
    expect(row).toHaveTextContent(SOURCE.uri);
    expect(row).toHaveTextContent("git");
    expect(row).toHaveTextContent("active");
    expect(screen.getByTestId(`last-run-${SOURCE.id}`)).toHaveTextContent("Never");
    expect(screen.getByTestId(`validation-badge-${SOURCE.id}`)).toHaveTextContent(
      "Not yet validated"
    );
    expect(screen.getByRole("button", { name: "Run" })).toBeInTheDocument();
  });

  it("shows an empty state when there are no sources", async () => {
    vi.spyOn(api, "listSources").mockResolvedValue([]);
    render(<SourcesScreen onRunStarted={() => {}} />);
    expect(await screen.findByTestId("sources-empty")).toBeInTheDocument();
  });

  it("shows an error state when listing sources fails", async () => {
    vi.spyOn(api, "listSources").mockRejectedValue(new Error("boom"));
    render(<SourcesScreen onRunStarted={() => {}} />);
    expect(await screen.findByTestId("sources-error")).toBeInTheDocument();
  });

  it("calls the dispatcher and navigates to the run view on Run", async () => {
    vi.spyOn(api, "listSources").mockResolvedValue([SOURCE]);
    const run = { id: "run-1", source_id: SOURCE.id, status: "queued" };
    const runSource = vi.spyOn(api, "runSource").mockResolvedValue(run);
    const onRunStarted = vi.fn();

    render(<SourcesScreen onRunStarted={onRunStarted} />);
    fireEvent.click(await screen.findByRole("button", { name: "Run" }));

    await waitFor(() => expect(onRunStarted).toHaveBeenCalledWith(run));
    expect(runSource).toHaveBeenCalledWith(SOURCE.id);
  });

  it("stays on the sources list and shows an error when Run fails", async () => {
    vi.spyOn(api, "listSources").mockResolvedValue([SOURCE]);
    vi.spyOn(api, "runSource").mockRejectedValue(new Error("boom"));
    const onRunStarted = vi.fn();

    render(<SourcesScreen onRunStarted={onRunStarted} />);
    fireEvent.click(await screen.findByRole("button", { name: "Run" }));

    expect(await screen.findByTestId("run-error")).toBeInTheDocument();
    expect(onRunStarted).not.toHaveBeenCalled();
    expect(screen.getByTestId("sources-table")).toBeInTheDocument();
  });
});
