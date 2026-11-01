"""Golden tasks for the workflow change-request impact agent.

Scenario (from DEMO_AGENTS.md):
  SQL repo has Table CUSTOMER.CUST_ID
  -> ETL Job (READS_FROM)
  -> Revenue Dashboard (DERIVED_FROM)
  Owner: data-engineering team

Pass condition: all known downstream assets and owners listed, none invented.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from agents.workflow.agent import WorkflowAgent
from agents.workflow.grounding import ContextClient
from agents.workflow.models import ChangeTicket, ImpactReport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ENTITY_ID_TABLE = "eid-table-001"
_ENTITY_ID_JOB = "eid-job-002"
_ENTITY_ID_DASH = "eid-dash-003"
_ENTITY_ID_TEAM = "eid-team-004"
_SOURCE_LINK = "https://github.com/demo/sql-repo"
_HARVESTED_AT = "2026-01-15T10:00:00"

_SEARCH_RESPONSE = [
    {
        "entity_id": _ENTITY_ID_TABLE,
        "entity_name": "CUSTOMER",
        "entity_type": "Table",
        "source_link": _SOURCE_LINK,
        "harvested_at": _HARVESTED_AT,
        "sensitivity": "internal",
    }
]

_LINEAGE_RESPONSE = {
    "root_entity_id": _ENTITY_ID_TABLE,
    "direction": "downstream",
    "nodes": [
        {
            "entity_id": _ENTITY_ID_TABLE,
            "entity_name": "CUSTOMER",
            "entity_type": "Table",
            "depth": 0,
            "source_link": _SOURCE_LINK,
            "harvested_at": _HARVESTED_AT,
            "sensitivity": "internal",
        },
        {
            "entity_id": _ENTITY_ID_JOB,
            "entity_name": "etl_customer_load",
            "entity_type": "Job",
            "depth": 1,
            "source_link": "https://github.com/demo/talend-repo",
            "harvested_at": _HARVESTED_AT,
            "sensitivity": "internal",
        },
        {
            "entity_id": _ENTITY_ID_DASH,
            "entity_name": "Revenue Dashboard",
            "entity_type": "Dashboard",
            "depth": 2,
            "source_link": "https://tableau.example.com/views/revenue",
            "harvested_at": _HARVESTED_AT,
            "sensitivity": "internal",
        },
    ],
    "edges": [
        {"src_entity_id": _ENTITY_ID_TABLE, "dst_entity_id": _ENTITY_ID_JOB, "relation": "READS_FROM", "confidence": 1.0},
        {"src_entity_id": _ENTITY_ID_JOB, "dst_entity_id": _ENTITY_ID_DASH, "relation": "DERIVED_FROM", "confidence": 1.0},
    ],
}

_RELATED_RESPONSE = [
    {
        "entity_id": _ENTITY_ID_TEAM,
        "entity_name": "data-engineering",
        "entity_type": "Team",
        "relation": "OWNED_BY",
        "direction": "out",
        "source_link": "https://github.com/demo/codeowners",
        "harvested_at": _HARVESTED_AT,
        "sensitivity": "internal",
    }
]

_LLM_RESPONSE = json.dumps({
    "suggested_approvers": ["data-engineering"],
    "suggested_tests": [
        "Verify etl_customer_load reads CUST_ID correctly after rename",
        "Run Revenue Dashboard smoke test",
    ],
    "draft_comment": (
        "Renaming CUSTOMER.CUST_ID will break etl_customer_load (Job) and transitively "
        "Revenue Dashboard. Approval required from data-engineering team."
    ),
})


def _make_context_client() -> ContextClient:
    transport = MagicMock()
    transport.get.side_effect = lambda url, params=None: (
        _SEARCH_RESPONSE if "/search" in url
        else _LINEAGE_RESPONSE if "/lineage/" in url
        else _RELATED_RESPONSE
    )
    return ContextClient("http://context-service", transport)


def _make_llm() -> MagicMock:
    llm = MagicMock()
    llm.complete.return_value = _LLM_RESPONSE
    return llm


# ---------------------------------------------------------------------------
# Golden task 1: rename-column scenario
# ---------------------------------------------------------------------------

@pytest.fixture()
def report() -> ImpactReport:
    ticket = ChangeTicket(
        entity_name="CUSTOMER",
        entity_type="Table",
        change_description="Rename column CUSTOMER.CUST_ID to CUSTOMER.CUSTOMER_ID",
    )
    agent = WorkflowAgent(_make_context_client(), _make_llm())
    return agent.run(ticket)


def test_downstream_job_present(report: ImpactReport) -> None:
    """etl_customer_load (Job) must appear in downstream assets."""
    names = [a.entity_name for a in report.downstream_assets]
    assert "etl_customer_load" in names, f"Job not found in {names}"


def test_downstream_dashboard_present(report: ImpactReport) -> None:
    """Revenue Dashboard must appear in downstream assets."""
    names = [a.entity_name for a in report.downstream_assets]
    assert "Revenue Dashboard" in names, f"Dashboard not found in {names}"


def test_owner_present(report: ImpactReport) -> None:
    """data-engineering team must appear as owner."""
    owner_names = [o.entity_name for o in report.owners]
    assert "data-engineering" in owner_names, f"Owner not found in {owner_names}"


def test_all_assets_have_citations(report: ImpactReport) -> None:
    """Every downstream asset must carry a citation with source_link and harvested_at."""
    for asset in report.downstream_assets:
        assert asset.citation.source_link, f"Missing source_link on {asset.entity_name}"
        assert asset.citation.harvested_at, f"Missing harvested_at on {asset.entity_name}"


def test_all_owners_have_citations(report: ImpactReport) -> None:
    """Every owner must carry a citation."""
    for owner in report.owners:
        assert owner.citation.source_link, f"Missing source_link on owner {owner.entity_name}"


def test_draft_comment_not_empty(report: ImpactReport) -> None:
    assert report.draft_comment


def test_suggested_approvers_not_empty(report: ImpactReport) -> None:
    assert report.suggested_approvers


# ---------------------------------------------------------------------------
# Golden task 2: no evidence scenario — nothing invented
# ---------------------------------------------------------------------------

def test_no_assets_invented_when_context_empty() -> None:
    """When the knowledge base has no results, the report must have no assets or owners."""
    transport = MagicMock()
    transport.get.return_value = []
    client = ContextClient("http://context-service", transport)
    llm = MagicMock()
    llm.complete.return_value = json.dumps({
        "suggested_approvers": [],
        "suggested_tests": [],
        "draft_comment": "No downstream impact found in the knowledge base.",
    })
    agent = WorkflowAgent(client, llm)
    result = agent.run(ChangeTicket("UNKNOWN_TABLE", "Table", "Drop table"))
    assert result.downstream_assets == [], "No assets should be present when context is empty"
    assert result.owners == [], "No owners should be present when context is empty"


# ---------------------------------------------------------------------------
# Golden task 3: lineage returns empty nodes — no assets invented
# ---------------------------------------------------------------------------

def test_no_assets_invented_when_lineage_empty() -> None:
    transport = MagicMock()
    transport.get.side_effect = lambda url, params=None: (
        _SEARCH_RESPONSE if "/search" in url
        else {"root_entity_id": _ENTITY_ID_TABLE, "nodes": [], "edges": []} if "/lineage/" in url
        else []
    )
    client = ContextClient("http://context-service", transport)
    llm = MagicMock()
    llm.complete.return_value = json.dumps({
        "suggested_approvers": [],
        "suggested_tests": [],
        "draft_comment": "No downstream impact found in the knowledge base.",
    })
    agent = WorkflowAgent(client, llm)
    result = agent.run(ChangeTicket("CUSTOMER", "Table", "Drop table"))
    assert result.downstream_assets == []
    assert result.owners == []
