import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { RunView } from "../src/components/RunView.jsx";

afterEach(cleanup);

describe("RunView", () => {
  it("shows the run id, source id and status", () => {
    render(<RunView run={{ id: "run-1", source_id: "src-1", status: "queued" }} />);

    expect(screen.getByTestId("run-id")).toHaveTextContent("run-1");
    expect(screen.getByTestId("run-source-id")).toHaveTextContent("src-1");
    expect(screen.getByTestId("run-status")).toHaveTextContent("queued");
  });
});
