import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { Skeleton } from "../src/components/Skeleton.jsx";

afterEach(cleanup);

describe("Skeleton", () => {
  it("renders the requested number of placeholders and no real content", () => {
    render(<Skeleton shape="row" count={3} />);
    expect(screen.getAllByTestId("skeleton-item")).toHaveLength(3);
  });

  it("defaults to a single row placeholder", () => {
    render(<Skeleton />);
    expect(screen.getAllByTestId("skeleton-item")).toHaveLength(1);
  });
});
