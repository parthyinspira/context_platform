"""context-retrieval MCP server (KAN-33).

Implements the MCP JSON-RPC protocol over HTTP (streamable HTTP transport).
Currently exposes: get_related.

Run with:
    uvicorn mcp_server.server:app --host 0.0.0.0 --port 8002
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp_server.db import get_connection_factory
from mcp_server.tools.get_related import get_related as _get_related

app = FastAPI(title="context-retrieval-mcp")

_TOOLS = [
    {
        "name": "get_related",
        "description": (
            "Traverse the knowledge graph from a starting entity up to `depth` hops, "
            "following edges in the given direction. Returns each reachable entity with "
            "the relation that connected it and a citation (source_link, harvested_at, "
            "sensitivity). Tombstoned entities are excluded. "
            "Use this to find owners, dependents, upstream/downstream assets, etc."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "UUID of the starting entity.",
                },
                "relation": {
                    "type": "string",
                    "description": (
                        "Optional relation label to restrict traversal "
                        "(e.g. DEPENDS_ON, READS_FROM, OWNED_BY)."
                    ),
                },
                "depth": {
                    "type": "integer",
                    "description": "Maximum number of hops (1–10, default 3).",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                },
                "direction": {
                    "type": "string",
                    "enum": ["out", "in", "both"],
                    "description": (
                        "Edge direction relative to each node visited: "
                        "'out' (outbound), 'in' (inbound), 'both' (default)."
                    ),
                    "default": "both",
                },
            },
            "required": ["entity_id"],
        },
    }
]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> JSONResponse:
    """Single MCP JSON-RPC endpoint (streamable HTTP transport)."""
    try:
        body = await request.json()
    except Exception:
        return _error_response(None, -32700, "Parse error")

    rpc_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    if method == "initialize":
        return _ok_response(rpc_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "context-retrieval", "version": "0.1.0"},
        })

    if method == "tools/list":
        return _ok_response(rpc_id, {"tools": _TOOLS})

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args: dict[str, Any] = params.get("arguments", {})
        if tool_name == "get_related":
            return _handle_get_related(rpc_id, tool_args)
        return _error_response(rpc_id, -32601, f"Unknown tool: {tool_name}")

    return _error_response(rpc_id, -32601, f"Method not found: {method}")


def _handle_get_related(rpc_id: Any, args: dict[str, Any]) -> JSONResponse:
    entity_id = args.get("entity_id")
    if not entity_id:
        return _error_response(rpc_id, -32602, "entity_id is required")

    relation: str | None = args.get("relation")
    depth: int = int(args.get("depth", 3))
    direction: str = args.get("direction", "both")

    depth = max(1, min(10, depth))

    conn_factory = get_connection_factory()
    conn = conn_factory()
    try:
        results = _get_related(
            conn,
            entity_id=entity_id,
            relation=relation,
            depth=depth,
            direction=direction,
        )
    finally:
        conn.close()

    content = json.dumps({"entities": results}, default=str)
    return _ok_response(rpc_id, {
        "content": [{"type": "text", "text": content}],
        "isError": False,
    })


def _ok_response(rpc_id: Any, result: Any) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})


def _error_response(rpc_id: Any, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": code, "message": message}},
        status_code=200,  # MCP errors are still HTTP 200
    )
