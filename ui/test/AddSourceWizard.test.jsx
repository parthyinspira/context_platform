import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/react";
import { AddSourceWizard } from "../src/components/AddSourceWizard.jsx";
import * as api from "../src/api.js";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function goToConnectStep() {
  fireEvent.click(screen.getByTestId("type-tile-git"));
}

describe("AddSourceWizard", () => {
  it("renders six type tiles with only Git enabled", () => {
    render(<AddSourceWizard />);
    const tiles = screen.getAllByTestId(/type-tile-/);
    expect(tiles).toHaveLength(6);
    expect(screen.getByTestId("type-tile-git")).not.toBeDisabled();
    expect(screen.getByTestId("type-tile-sql")).toBeDisabled();
  });

  it("advances to the connect step after selecting Git", () => {
    render(<AddSourceWizard />);
    goToConnectStep();
    expect(screen.getByTestId("wizard-step-connect")).toBeInTheDocument();
  });

  it("shows a loading indicator while test connection is in flight", () => {
    render(<AddSourceWizard />);
    goToConnectStep();
    vi.spyOn(api, "testConnection").mockReturnValue(new Promise(() => {}));
    fireEvent.click(screen.getByTestId("test-connection-button"));
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("shows success and blanks the credentials field after a successful test", async () => {
    render(<AddSourceWizard />);
    goToConnectStep();
    vi.spyOn(api, "testConnection").mockResolvedValue({ ok: true, error: null });

    fireEvent.change(screen.getByTestId("connect-credentials-input"), {
      target: { value: "super-secret-token" },
    });
    fireEvent.click(screen.getByTestId("test-connection-button"));

    await screen.findByTestId("connect-success");
    expect(screen.getByTestId("connect-credentials-input").value).toBe("");
  });

  it("shows an error message when test connection fails", async () => {
    render(<AddSourceWizard />);
    goToConnectStep();
    vi.spyOn(api, "testConnection").mockResolvedValue({ ok: false, error: "bad credentials" });

    fireEvent.click(screen.getByTestId("test-connection-button"));

    const banner = await screen.findByTestId("error-banner");
    expect(banner).toHaveTextContent("bad credentials");
  });

  it("creates the source with the tested credentials on Add source", async () => {
    render(<AddSourceWizard onSourceCreated={vi.fn()} />);
    goToConnectStep();
    fireEvent.change(screen.getByTestId("connect-uri-input"), {
      target: { value: "https://github.com/example/repo.git" },
    });
    vi.spyOn(api, "testConnection").mockResolvedValue({ ok: true, error: null });
    fireEvent.change(screen.getByTestId("connect-credentials-input"), {
      target: { value: "super-secret-token" },
    });
    fireEvent.click(screen.getByTestId("test-connection-button"));
    await screen.findByTestId("connect-success");

    const createSource = vi.spyOn(api, "createSource").mockResolvedValue({ id: "src-1" });
    vi.spyOn(api, "discoverSource").mockReturnValue(new Promise(() => {}));
    fireEvent.click(screen.getByTestId("add-source-submit"));

    await waitFor(() =>
      expect(createSource).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "git",
          uri: "https://github.com/example/repo.git",
          credentials_ref: "super-secret-token",
        })
      )
    );
  });
});
