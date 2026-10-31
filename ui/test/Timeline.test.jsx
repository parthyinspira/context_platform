import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { Timeline } from "../src/components/Timeline.jsx";

afterEach(cleanup);

const stages = [
  { id: "connect", name: "Connect", status: "done" },
  { id: "fetch", name: "Fetch", status: "active" },
  { id: "publish", name: "Publish", status: "pending" },
];

describe("Timeline", () => {
  it("renders each stage in order with its status", () => {
    render(<Timeline state="success" stages={stages} />);
    const items = screen.getAllByTestId("timeline-stage");
    expect(items).toHaveLength(3);
    expect(items[0]).toHaveAttribute("data-status", "done");
    expect(items[1]).toHaveAttribute("data-status", "active");
    expect(items[2]).toHaveAttribute("data-status", "pending");
  });

  it("shows skeleton stages in the loading state", () => {
    render(<Timeline state="loading" stages={stages} />);
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("shows an error banner in the error state", () => {
    render(<Timeline state="error" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows an empty state with no run started", () => {
    render(<Timeline state="empty" />);
    expect(screen.getByTestId("empty-state")).toHaveTextContent("No run started");
  });
});
