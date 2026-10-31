import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { App } from "../src/App.jsx";

afterEach(cleanup);

describe("App shell", () => {
  it("renders a nav rail with the five sections and a top bar", () => {
    render(<App />);

    const nav = screen.getByTestId("nav-rail");
    for (const item of ["Graph", "Sources", "Runs", "Agents", "Settings"]) {
      expect(nav).toHaveTextContent(item);
    }

    expect(screen.getByTestId("top-bar")).toBeInTheDocument();
  });

  it("toggles the document theme between light and dark", () => {
    render(<App />);

    expect(document.documentElement.getAttribute("data-theme")).toBe("light");

    const toggle = screen.getByTestId("theme-toggle");
    fireEvent.click(toggle);
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");

    fireEvent.click(toggle);
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });
});
