"""Unit tests for all four demo agents.

Each test verifies:
- Required node IDs are retrieved
- Citations are non-empty (or correctly empty on escalation)
- Answer is deterministic for the same task key
"""
import pytest

from agents.workflow import demo_agent as workflow_agent
from agents.research import agent as research_agent
from agents.prod_support import agent as prod_support_agent
from agents.call_centre import agent as call_centre_agent


class TestWorkflowAgent:
    def test_run_returns_result(self):
        result = workflow_agent.run("rename-cust-id")
        assert result.agent == "workflow"
        assert result.answer

    def test_downstream_assets_found(self):
        result = workflow_agent.run("rename-cust-id")
        # REVENUE_DAILY and Revenue Dashboard should be found downstream
        assert "tbl-revenue" in result.retrieved_node_ids
        assert "dash-revenue" in result.retrieved_node_ids

    def test_owners_found(self):
        result = workflow_agent.run("rename-cust-id")
        # Alice Eng and Data Engineering team should be found as owners
        assert "person-data-eng" in result.retrieved_node_ids or "team-data" in result.retrieved_node_ids

    def test_citations_non_empty(self):
        result = workflow_agent.run("rename-cust-id")
        assert len(result.citations) > 0

    def test_deterministic(self):
        r1 = workflow_agent.run("rename-cust-id")
        r2 = workflow_agent.run("rename-cust-id")
        assert r1.retrieved_node_ids == r2.retrieved_node_ids


class TestResearchAgent:
    def test_run_returns_result(self):
        result = research_agent.run("customer-to-revenue")
        assert result.agent == "research"

    def test_false_claim_flagged(self):
        result = research_agent.run("customer-to-revenue")
        assert "UNVERIFIED" in result.answer

    def test_asset_chain_retrieved(self):
        result = research_agent.run("customer-to-revenue")
        # Should retrieve service, customer table, and downstream assets
        ids = result.retrieved_node_ids
        assert "tbl-customer" in ids
        assert "dash-revenue" in ids

    def test_citations_non_empty(self):
        result = research_agent.run("customer-to-revenue")
        assert len(result.citations) > 0


class TestProdSupportAgent:
    def test_run_returns_result(self):
        result = prod_support_agent.run("stale-revenue-dashboard")
        assert result.agent == "prod_support"

    def test_broken_job_in_top_causes(self):
        result = prod_support_agent.run("stale-revenue-dashboard")
        # The broken upstream job must appear in the answer
        assert "etl_weekly_transform" in result.answer

    def test_broken_job_node_retrieved(self):
        result = prod_support_agent.run("stale-revenue-dashboard")
        assert "job-broken-etl" in result.retrieved_node_ids

    def test_runbook_cited(self):
        result = prod_support_agent.run("stale-revenue-dashboard")
        assert any("runbook" in c.source_url.lower() for c in result.citations)


class TestCallCentreAgent:
    def test_in_scope_returns_answer(self):
        result = call_centre_agent.run("mid-year-contribution")
        assert result.agent == "call_centre"
        assert not result.escalated
        assert len(result.citations) > 0

    def test_in_scope_answer_has_source(self):
        result = call_centre_agent.run("mid-year-contribution")
        assert "Source URL" in result.answer
        assert "restricted" not in result.answer.lower() or "No restricted" in result.answer

    def test_out_of_scope_escalates(self):
        result = call_centre_agent.run("out-of-scope")
        assert result.escalated
        assert len(result.citations) == 0

    def test_no_restricted_content_for_internal_caller(self):
        result = call_centre_agent.run("mid-year-contribution")
        # doc-restricted should never appear in citations
        assert not any(c.entity_id == "doc-restricted" for c in result.citations)
