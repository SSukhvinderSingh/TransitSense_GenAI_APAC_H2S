#!/usr/bin/env python3
"""Tests for NL Query Router Skill."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skills.query_router import parse_query


def test_delay_analysis_intent():
    result = parse_query("why is route 219 always late on Fridays?")
    assert result["target_skill"] == "delay_analysis"
    assert result["route_id"] == "219"


def test_priority_scoring_intent():
    result = parse_query("what is the worst route right now?")
    assert result["target_skill"] == "priority_scoring"


def test_forecast_intent():
    result = parse_query("predict ridership for route 49M next week")
    assert result["target_skill"] == "forecast"
    assert result["route_id"] == "49M"
    assert result["metric"] == "ridership"


def test_ambiguous_query():
    result = parse_query("what")
    assert result["target_skill"] == "clarify"


def test_greeting_intent():
    for q in ["hello", "hi", "hey", "good morning"]:
        result = parse_query(q)
        assert result["target_skill"] == "greeting", f"'{q}' should be greeting"


def test_forecast_delay_default_metric():
    result = parse_query("forecast delays for route 113M")
    assert result["target_skill"] == "forecast"
    assert result["route_id"] == "113M"
    assert result["metric"] == "delay"


def test_delay_with_date_range():
    result = parse_query("delay stats for route 219 from 2026-06-01 to 2026-06-30")
    assert result["target_skill"] == "delay_analysis"
    assert result["route_id"] == "219"
    assert result["date_range"] == ["2026-06-01", "2026-06-30"]
