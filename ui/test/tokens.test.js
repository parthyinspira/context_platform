import { describe, it, expect } from "vitest";
import tokens from "../src/tokens.json";

const requiredKeys = [
  "bg.canvas",
  "bg.surface",
  "border.subtle",
  "text.primary",
  "text.secondary",
  "accent",
  "success",
  "warning",
  "danger",
];

describe("tokens.json", () => {
  it("defines both a light and a dark theme", () => {
    expect(tokens.light).toBeTruthy();
    expect(tokens.dark).toBeTruthy();
  });

  it.each(requiredKeys)("light theme defines %s", (key) => {
    expect(typeof tokens.light[key]).toBe("string");
  });

  it.each(requiredKeys)("dark theme defines %s", (key) => {
    expect(typeof tokens.dark[key]).toBe("string");
  });

  it("uses different values between light and dark", () => {
    expect(tokens.light["bg.canvas"]).not.toBe(tokens.dark["bg.canvas"]);
    expect(tokens.light["text.primary"]).not.toBe(tokens.dark["text.primary"]);
  });
});
