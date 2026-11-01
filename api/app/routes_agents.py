"""Demo agent endpoint — deterministic, no live LLM or DB needed."""
from __future__ import annotations

import dataclasses
import sys
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# agents/ is at the repo root, not inside api/; add it to the path.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from agents.workflow import demo_agent as workflow_agent
from agents.research import agent as research_agent
from agents.prod_support import agent as prod_support_agent
from agents.call_centre import agent as call_centre_agent

router = APIRouter()

_AGENTS: dict[str, Any] = {
    "workflow": workflow_agent,
    "research": research_agent,
    "prod_support": prod_support_agent,
    "call_centre": call_centre_agent,
}


class AgentRunRequest(BaseModel):
    task_key: str


@router.post("/agents/{agent_name}/run")
def run_agent(agent_name: str, req: AgentRunRequest) -> dict:
    module = _AGENTS.get(agent_name)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    try:
        result = module.run(req.task_key)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown task_key '{req.task_key}' for agent '{agent_name}'")
    return dataclasses.asdict(result)
