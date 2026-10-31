import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { Badge } from "../src/components/Badge.jsx";

afterEach(cleanup);

describe("Badge", () => {
  it("renders each variant with an icon and label in the success state", () => {
    for (const variant of ["success", "warning", "danger", "info"]) {
      cleanup();
      render(<Badge state="success" variant={variant} label="Published" />);
      const badge = screen.getByTestId("badge");
      expect(badge).toHaveAttribute("data-variant", variant);
      expect(badge).toHaveTextContent("Published");
    }
  });

  it("shows a skeleton in the loading state", () => {
    render(<Badge state="loading" />);
    expect(screen.getByTestId("badge")).toHaveAttribute("data-state", "loading");
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("shows an error banner in the error state", () => {
    render(<Badge state="error" />);
    expect(screen.getByTestId("badge")).toHaveAttribute("data-state", "error");
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows an empty placeholder in the empty state", () => {
    render(<Badge state="empty" />);
    expect(screen.getByTestId("badge")).toHaveAttribute("data-state", "empty");
    expect(screen.getByTestId("empty-state")).toHaveTextContent("No status");
  });
});
