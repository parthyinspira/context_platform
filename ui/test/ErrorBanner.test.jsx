import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { ErrorBanner } from "../src/components/ErrorBanner.jsx";

afterEach(cleanup);

describe("ErrorBanner", () => {
  it("renders the error message with an alert role", () => {
    render(<ErrorBanner message="Could not reach the server" />);
    const banner = screen.getByRole("alert");
    expect(banner).toHaveTextContent("Could not reach the server");
  });

  it("falls back to a default message", () => {
    render(<ErrorBanner />);
    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong");
  });
});
