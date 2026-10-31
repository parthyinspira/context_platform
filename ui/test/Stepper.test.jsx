import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { Stepper } from "../src/components/Stepper.jsx";

afterEach(cleanup);

const steps = [
  { id: "type", label: "Type" },
  { id: "connect", label: "Connect" },
  { id: "discover", label: "Discover" },
];

describe("Stepper", () => {
  it("marks earlier steps complete and the active step current", () => {
    render(<Stepper state="success" steps={steps} activeStep={1} />);
    const items = screen.getAllByTestId("stepper-step");
    expect(items[0]).toHaveAttribute("data-status", "complete");
    expect(items[1]).toHaveAttribute("data-status", "current");
    expect(items[1]).toHaveAttribute("aria-current", "step");
    expect(items[2]).toHaveAttribute("data-status", "pending");
  });

  it("shows skeleton steps in the loading state", () => {
    render(<Stepper state="loading" steps={steps} />);
    expect(screen.getByTestId("stepper")).toHaveAttribute("data-state", "loading");
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("shows an error banner in the error state", () => {
    render(<Stepper state="error" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows an empty state with no steps configured", () => {
    render(<Stepper state="empty" />);
    expect(screen.getByTestId("empty-state")).toHaveTextContent("No steps configured");
  });
});
