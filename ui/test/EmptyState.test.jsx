import { describe, it, expect, afterEach, vi } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { EmptyState } from "../src/components/EmptyState.jsx";

afterEach(cleanup);

describe("EmptyState", () => {
  it("renders the message", () => {
    render(<EmptyState message="Nothing here" />);
    expect(screen.getByTestId("empty-state")).toHaveTextContent("Nothing here");
  });

  it("renders and triggers the optional action", () => {
    const onAction = vi.fn();
    render(<EmptyState message="Nothing here" actionLabel="Add a source" onAction={onAction} />);
    fireEvent.click(screen.getByText("Add a source"));
    expect(onAction).toHaveBeenCalledOnce();
  });
});
