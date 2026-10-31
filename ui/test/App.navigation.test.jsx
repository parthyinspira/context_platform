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

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Sources" }));
    await screen.findByTestId("sources-table");

    fireEvent.click(await screen.findByRole("button", { name: "Run" }));

    await waitFor(() => expect(screen.getByTestId("run-view")).toBeInTheDocument());
    expect(screen.getByTestId("run-id")).toHaveTextContent("run-1");
  });
});
