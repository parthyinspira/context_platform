import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distDir = path.join(__dirname, "dist");

const MIME_TYPES = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
};

export function createServer() {
  return http.createServer(async (req, res) => {
    if (req.url === "/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "ok" }));
      return;
    }

    const requestedPath = req.url === "/" ? "/index.html" : req.url;
    const filePath = path.join(distDir, requestedPath);

    try {
      const body = await readFile(filePath);
      const ext = path.extname(filePath);
      res.writeHead(200, { "Content-Type": MIME_TYPES[ext] || "application/octet-stream" });
      res.end(body);
    } catch {
      try {
        const indexBody = await readFile(path.join(distDir, "index.html"));
        res.writeHead(200, { "Content-Type": "text/html" });
        res.end(indexBody);
      } catch {
        res.writeHead(404, { "Content-Type": "text/plain" });
        res.end("not found");
      }
    }
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const port = process.env.PORT || 3000;
  createServer().listen(port, () => {
    console.log(`ui listening on ${port}`);
  });
}
