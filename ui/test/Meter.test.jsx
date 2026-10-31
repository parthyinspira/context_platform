import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { Meter } from "../src/components/Meter.jsx";

afterEach(cleanup);

describe("Meter", () => {
  it("renders a labelled progress bar with numeric value and max", () => {
    render(<Meter state="success" label="Files" value={25} max={100} />);
    const bar = screen.getByRole("progressbar", { name: "Files" });
    expect(bar).toHaveAttribute("aria-valuenow", "25");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
    expect(screen.getByText("25 / 100")).toBeInTheDocument();
  });

  it("shows a skeleton bar in the loading state", () => {
    render(<Meter state="loading" label="Files" />);
    expect(screen.getByTestId("meter")).toHaveAttribute("data-state", "loading");
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("shows an error banner in the error state", () => {
    render(<Meter state="error" label="Files" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows an empty state with no budget set", () => {
    render(<Meter state="empty" label="Files" />);
    expect(screen.getByTestId("empty-state")).toHaveTextContent("No budget set");
  });
});
