import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "../server.js";

test("GET /health returns ok", async () => {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  const response = await fetch(`http://localhost:${port}/health`);
  const body = await response.json();

  assert.equal(response.status, 200);
  assert.deepEqual(body, { status: "ok" });

  server.close();
});
