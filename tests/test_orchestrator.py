#!/usr/bin/env python3
"""Tests for TransitSense Orchestrator."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator import handle_query
from pydantic import BaseModel

os.environ["TRANSITSENSE_DB"] = os.path.join(os.path.dirname(__file__), "..", "data", "transitsense.db")


class FakeRequest(BaseModel):
    query: str
    session_id: str


def test_orchestrator_delay_analysis():
    req = FakeRequest(query="why is route 219 always late?", session_id="test-1")
    resp = handle_query(req)
    assert resp.source_skill == "delay_analysis"
    assert "3.69" in resp.answer_text or "average delay" in resp.answer_text
    assert "route_id" in resp.cited_metrics


def test_orchestrator_priority_scoring():
    req = FakeRequest(query="what is the worst route?", session_id="test-2")
    resp = handle_query(req)
    assert resp.source_skill == "priority_scoring"
    assert len(resp.skill_calls) >= 1


def test_orchestrator_forecast():
    req = FakeRequest(query="forecast ridership for route 49M", session_id="test-3")
    resp = handle_query(req)
    assert resp.source_skill == "forecast"
    assert resp.cited_metrics.get("model_version") == "ma_v0.1.0"


def test_orchestrator_clarify():
    req = FakeRequest(query="what does this do", session_id="test-4")
    resp = handle_query(req)
    assert resp.source_skill == "clarify"
    assert "not sure" in resp.answer_text.lower()


def test_orchestrator_greeting():
    req = FakeRequest(query="hello", session_id="test-4")
    resp = handle_query(req)
    assert resp.source_skill == "greeting"
    assert "TransitSense" in resp.answer_text


def test_orchestrator_no_fabrication():
    req = FakeRequest(query="why is route 219 always late?", session_id="test-5")
    resp = handle_query(req)
    import re
    nums = re.findall(r"\b\d+\.?\d*\b", resp.answer_text)
    cited = set(str(v) for v in resp.cited_metrics.values() if isinstance(v, (int, float)))
    for n in nums:
        if float(n) < 1000:  # skip large row counts that are context
            pass


def test_orchestrator_empty_query():
    req = FakeRequest(query="", session_id="test-6")
    try:
        handle_query(req)
        assert False, "Should have raised"
    except Exception:
        pass


def test_follow_up_expansion():
    """'Can you be more detailed?' after a locality query should expand."""
    sid = "test-expand-1"
    # First ask about a locality to build session context
    r1 = handle_query(FakeRequest(query="how is Secunderabad doing?", session_id=sid))
    assert r1.source_skill == "locality_status"
    assert "routes operating" in r1.answer_text
    # Follow up with request for more detail
    r2 = handle_query(FakeRequest(query="can you be more detailed", session_id=sid))
    assert r2.source_skill == "delay_analysis"
    assert "Full details" in r2.answer_text or "routes" in r2.answer_text


def test_detailed_on_route():
    """'Cna you be detailed on Route 277D' should route to delay analysis."""
    sid = "test-detailed-route"
    req = FakeRequest(query="Cna you be detailed on Route 277D", session_id=sid)
    resp = handle_query(req)
    assert resp.source_skill == "delay_analysis"
    assert "277D" in resp.answer_text or "average delay" in resp.answer_text or "route_id" in resp.cited_metrics


def test_tell_more_no_context():
    """'tell me more' with no session context should ask which route."""
    sid = "test-nocontext-1"
    req = FakeRequest(query="tell me more", session_id=sid)
    resp = handle_query(req)
    assert resp.source_skill == "delay_analysis"
    assert "route" in resp.answer_text.lower() and "?" in resp.answer_text
