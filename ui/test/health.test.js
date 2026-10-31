import { describe, it, expect } from "vitest";
import { createServer } from "../server.js";

describe("GET /health", () => {
  it("returns ok", async () => {
    const server = createServer();
    await new Promise((resolve) => server.listen(0, resolve));
    const { port } = server.address();

    const response = await fetch(`http://localhost:${port}/health`);
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body).toEqual({ status: "ok" });

    server.close();
  });
});
