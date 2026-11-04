"""context-retrieval MCP server — streamable HTTP transport."""
import os
from typing import Any

import psycopg
from mcp.server.fastmcp import FastMCP

from search import search_context

mcp = FastMCP("context-retrieval", host="0.0.0.0", port=8080)


def _get_conn() -> Any:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be set")
    return psycopg.connect(url)


@mcp.tool()
def search_context_tool(query: str, limit: int = 5) -> list[dict]:
    """Search indexed content. Returns results with source_link, harvested_at and sensitivity."""
    conn = _get_conn()
    try:
        results = search_context(conn, query, limit)
    finally:
        conn.close()
    return [
        {
            "text": r.text,
            "source_link": r.source_link,
            "harvested_at": r.harvested_at,
            "sensitivity": r.sensitivity,
        }
        for r in results
    ]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
