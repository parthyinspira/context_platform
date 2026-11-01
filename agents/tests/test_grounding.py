"""Tests for agents/grounding.py — search, expand, freshness, refuse/escalate."""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

from agents.grounding import Citation, Claim, GroundedAnswer, ground


def _make_chunk(
    text: str = "example text",
    source_link: str = "https://example.com/repo",
    harvested_at: str | None = None,
    sensitivity: str = "internal",
    entity_id: str = "e1",
    chunk_id: str = "c1",
    score: float = 0.9,
) -> dict:
    if harvested_at is None:
        harvested_at = datetime.datetime.utcnow().isoformat()
    return {
        "chunk_id": chunk_id,
        "text": text,
        "harvested_at": harvested_at,
        "entity_id": entity_id,
        "entity_type": "Document",
        "entity_name": "Test Doc",
        "source_link": source_link,
        "sensitivity": sensitivity,
        "score": score,
    }


def _stub_llm(claim_text: str = "The answer is X.") -> MagicMock:
    llm = MagicMock()
    llm.complete.return_value = claim_text
    return llm


def test_ground_returns_cited_answer():
    """ground() returns a GroundedAnswer with at least one Claim with a Citation."""
    chunk = _make_chunk(text="Customer table holds customer records.")
    llm = _stub_llm("Customer table holds customer records.")

    with patch("agents.grounding.hybrid_search", return_value=[chunk]):
        result = ground("customer table", conn=None, llm=llm)

    assert isinstance(result, GroundedAnswer)
    assert not result.refused
    assert len(result.claims) >= 1
    for claim in result.claims:
        assert isinstance(claim, Claim)
        assert len(claim.citations) >= 1
        for cit in claim.citations:
            assert isinstance(cit, Citation)
            assert cit.source_link
            assert cit.harvested_at


def test_ground_refuses_when_no_evidence():
    """ground() refuses with refused=True and no claims when search returns nothing."""
    llm = _stub_llm()

    with patch("agents.grounding.hybrid_search", return_value=[]):
        result = ground("unknown query", conn=None, llm=llm)

    assert result.refused is True
    assert result.refused_reason == "no_evidence"
    assert result.claims == []
    llm.complete.assert_not_called()


def test_claims_separated_from_evidence():
    """GroundedAnswer.evidence holds raw chunks; claims are separate typed objects."""
    chunk = _make_chunk()
    llm = _stub_llm("Chunk text.")

    with patch("agents.grounding.hybrid_search", return_value=[chunk]):
        result = ground("q", conn=None, llm=llm)

    assert result.evidence is not None
    assert len(result.evidence) >= 1
    assert result.evidence[0]["chunk_id"] == chunk["chunk_id"]
    assert all(isinstance(c, Claim) for c in result.claims)


def test_stale_chunk_labelled():
    """Citation.stale is True when harvested_at is older than the threshold."""
    old_time = (datetime.datetime.utcnow() - datetime.timedelta(hours=50)).isoformat()
    chunk = _make_chunk(harvested_at=old_time)
    llm = _stub_llm("Some claim.")

    with patch("agents.grounding.hybrid_search", return_value=[chunk]):
        result = ground("q", conn=None, llm=llm, freshness_threshold_hours=24)

    assert result.refused is False
    all_citations = [cit for claim in result.claims for cit in claim.citations]
    assert any(cit.stale for cit in all_citations)


def test_fresh_chunk_not_stale():
    """Citation.stale is False when harvested_at is within the threshold."""
    recent = datetime.datetime.utcnow().isoformat()
    chunk = _make_chunk(harvested_at=recent)
    llm = _stub_llm("Some claim.")

    with patch("agents.grounding.hybrid_search", return_value=[chunk]):
        result = ground("q", conn=None, llm=llm, freshness_threshold_hours=24)

    all_citations = [cit for claim in result.claims for cit in claim.citations]
    assert all(not cit.stale for cit in all_citations)


def test_expand_calls_lineage():
    """ground() calls get_lineage to expand context when conn is provided."""
    chunk = _make_chunk(entity_id="e1")
    llm = _stub_llm("X depends on Y.")

    mock_conn = MagicMock()
    lineage_nodes = [{"entity_id": "e2", "entity_type": "Table", "entity_name": "T2", "depth": 1}]

    with (
        patch("agents.grounding.hybrid_search", return_value=[chunk]),
        patch("agents.grounding.get_lineage", return_value=(lineage_nodes, [])) as mock_lin,
    ):
        result = ground("q", conn=mock_conn, llm=llm)

    mock_lin.assert_called()
    assert not result.refused
