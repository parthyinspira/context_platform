"""POST /agents/chat — agentic chat with tool execution.

The endpoint runs a full Anthropic tool-use loop:
  1. Send user message + system prompt to Claude.
  2. When Claude requests a tool, execute it against the local knowledge graph.
  3. Feed the result back and repeat until Claude returns a final text answer.

Built-in tools mirror the MCP surface (search_context, get_entity, get_graph,
list_sources). External MCP server URLs can be passed in `extra_tool_servers`;
their tools are fetched and proxied through httpx.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.main import connection_factory_dependency

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Tool definitions sent to Claude ──────────────────────────────────────────

BUILTIN_TOOLS = [
    {
        "name": "search_context",
        "description": "Full-text search over indexed knowledge graph chunks. Returns matching text with source links and harvested_at timestamps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_entity",
        "description": "Look up a single entity by name or partial name. Returns type, props and source.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Entity name (partial match ok)"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_graph",
        "description": "Return entities and edges. Optionally filter by entity name or type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name_filter": {"type": "string", "description": "Filter entity names (optional)"},
                "type_filter": {"type": "string", "description": "Filter entity type, e.g. Table, Module (optional)"},
                "limit": {"type": "integer", "description": "Max entities (default 20)", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name": "list_sources",
        "description": "List all registered data sources with their type, URI, status and last harvest time.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ── Tool executors ────────────────────────────────────────────────────────────

def _run_search_context(conn: Any, query: str, limit: int = 5) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.text, e.name, s.uri, c.harvested_at, s.sensitivity
        FROM chunks c
        JOIN entities e ON e.id = c.entity_id
        JOIN sources s ON s.id = c.source_id
        WHERE c.text ILIKE %s
        ORDER BY c.harvested_at DESC
        LIMIT %s
        """,
        (f"%{query}%", limit),
    )
    rows = cur.fetchall()
    return [
        {"text": r[0][:500], "entity": r[1], "source_uri": r[2],
         "harvested_at": str(r[3])[:10] if r[3] else None, "sensitivity": r[4]}
        for r in rows
    ]


def _run_get_entity(conn: Any, name: str) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, type, name, props, source_id FROM entities WHERE name ILIKE %s AND tombstoned_at IS NULL LIMIT 5",
        (f"%{name}%",),
    )
    rows = cur.fetchall()
    return [
        {"id": str(r[0]), "type": r[1], "name": r[2],
         "props": (r[3] if isinstance(r[3], dict) else json.loads(r[3])) if r[3] else {},
         "source_id": str(r[4])}
        for r in rows
    ]


def _run_get_graph(conn: Any, name_filter: str = "", type_filter: str = "", limit: int = 20) -> dict:
    cur = conn.cursor()
    clauses = ["tombstoned_at IS NULL"]
    params: list[Any] = []
    if name_filter:
        clauses.append("name ILIKE %s")
        params.append(f"%{name_filter}%")
    if type_filter:
        clauses.append("type = %s")
        params.append(type_filter)
    params.append(limit)
    cur.execute(
        f"SELECT id, type, name, source_id FROM entities WHERE {' AND '.join(clauses)} LIMIT %s",
        params,
    )
    entities = [{"id": str(r[0]), "type": r[1], "name": r[2], "source_id": str(r[3])} for r in cur.fetchall()]
    entity_ids = [e["id"] for e in entities]
    edges: list[dict] = []
    if entity_ids:
        placeholders = ",".join(["%s"] * len(entity_ids))
        cur.execute(
            f"SELECT src_entity_id, dst_entity_id, relation, confidence FROM edges WHERE src_entity_id IN ({placeholders}) OR dst_entity_id IN ({placeholders})",
            entity_ids + entity_ids,
        )
        edges = [{"src": str(r[0]), "dst": str(r[1]), "relation": r[2], "confidence": float(r[3])} for r in cur.fetchall()]
    return {"entities": entities, "edges": edges}


def _run_list_sources(conn: Any) -> list[dict]:
    cur = conn.cursor()
    cur.execute("SELECT id, type, uri, status, last_harvest_at FROM sources WHERE status != 'disabled' ORDER BY id")
    return [
        {"id": str(r[0]), "type": r[1], "uri": r[2], "status": r[3],
         "last_harvest_at": str(r[4])[:19] if r[4] else None}
        for r in cur.fetchall()
    ]


def _execute_builtin(conn: Any, tool_name: str, tool_input: dict) -> str:
    try:
        if tool_name == "search_context":
            result = _run_search_context(conn, tool_input.get("query", ""), tool_input.get("limit", 5))
        elif tool_name == "get_entity":
            result = _run_get_entity(conn, tool_input.get("name", ""))
        elif tool_name == "get_graph":
            result = _run_get_graph(conn, tool_input.get("name_filter", ""), tool_input.get("type_filter", ""), tool_input.get("limit", 20))
        elif tool_name == "list_sources":
            result = _run_list_sources(conn)
        else:
            return f"Unknown tool: {tool_name}"
        return json.dumps(result, default=str)
    except Exception as exc:
        logger.warning("tool %s failed: %s", tool_name, exc)
        return json.dumps({"error": str(exc)})


# ── External MCP server proxy ─────────────────────────────────────────────────

def _fetch_external_tools(server_url: str) -> list[dict]:
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{server_url.rstrip('/')}/tools")
            resp.raise_for_status()
            tools = resp.json()
            if isinstance(tools, list):
                return tools
            return tools.get("tools", [])
    except Exception as exc:
        logger.warning("external MCP tools fetch failed %s: %s", server_url, exc)
        return []


def _call_external_tool(server_url: str, tool_name: str, tool_input: dict) -> str:
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{server_url.rstrip('/')}/tools/{tool_name}",
                json=tool_input,
            )
            resp.raise_for_status()
            return json.dumps(resp.json())
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Route ─────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    system_prompt: str = "You are a helpful assistant with access to a knowledge graph. Answer questions using the available tools and always cite your sources."
    model: str = "claude-sonnet-4-5"
    enabled_tools: list[str] = []
    extra_tool_servers: list[str] = []


class ToolCallRecord(BaseModel):
    tool: str
    input: dict
    result: str


class ChatResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallRecord]
    model: str


@router.post("/agents/chat", response_model=ChatResponse)
def agent_chat(
    req: ChatRequest,
    connection_factory: Any = Depends(connection_factory_dependency),
) -> ChatResponse:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ChatResponse(
            answer="⚠️ ANTHROPIC_API_KEY is not set. Add it to your .env file and restart the API container.",
            tool_calls=[], model=req.model,
        )

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    conn = connection_factory()

    # Build tool list
    enabled = set(req.enabled_tools) if req.enabled_tools else {t["name"] for t in BUILTIN_TOOLS}
    tools = [t for t in BUILTIN_TOOLS if t["name"] in enabled]

    # Fetch external MCP tools
    external_tool_map: dict[str, str] = {}  # tool_name -> server_url
    for server_url in req.extra_tool_servers:
        for ext_tool in _fetch_external_tools(server_url):
            tname = ext_tool.get("name", "")
            if tname and tname not in enabled:
                tools.append(ext_tool)
                external_tool_map[tname] = server_url

    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    tool_calls_log: list[ToolCallRecord] = []

    # Agentic loop — max 6 rounds to prevent runaway
    for _ in range(6):
        kwargs: dict[str, Any] = dict(
            model=req.model,
            max_tokens=2048,
            system=req.system_prompt,
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools

        response = client.messages.create(**kwargs)

        if response.stop_reason == "end_turn":
            answer = " ".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            conn.close()
            return ChatResponse(answer=answer, tool_calls=tool_calls_log, model=req.model)

        if response.stop_reason == "tool_use":
            # Append assistant message with all content blocks
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tname = block.name
                tinput = block.input or {}
                if tname in external_tool_map:
                    result_str = _call_external_tool(external_tool_map[tname], tname, tinput)
                else:
                    result_str = _execute_builtin(conn, tname, tinput)
                tool_calls_log.append(ToolCallRecord(tool=tname, input=tinput, result=result_str))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    conn.close()
    answer = " ".join(
        block.text for block in response.content if hasattr(block, "text")
    ) or "(no response)"
    return ChatResponse(answer=answer, tool_calls=tool_calls_log, model=req.model)
