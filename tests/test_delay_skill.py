#!/usr/bin/env python3
"""Tests for Delay Analysis Skill."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skills.delay_analysis import get_delay_stats, MIN_DATA_POINTS


DB = os.path.join(os.path.dirname(__file__), "..", "data", "transitsense.db")


def test_delay_stats_known_route():
    os.environ["TRANSITSENSE_DB"] = DB
    result = get_delay_stats("219", ("2026-06-01", "2026-06-30"))
    assert result["route_id"] == "219"
    assert result["insufficient_data"] is False
    assert isinstance(result["avg_delay_min"], float)
    assert 0 <= result["on_time_pct"] <= 100
    assert result["row_count"] > 0


def test_delay_stats_insufficient_data():
    os.environ["TRANSITSENSE_DB"] = DB
    result = get_delay_stats("NONEXISTENT_ROUTE")
    assert result["insufficient_data"] is True
    assert result["row_count"] == 0


def test_delay_stats_anomaly_flags():
    os.environ["TRANSITSENSE_DB"] = DB
    result = get_delay_stats("219", ("2026-06-01", "2026-06-30"))
    if result["anomaly_flags"]:
        flag = result["anomaly_flags"][0]
        assert "trip_id" in flag
        assert "delay_min" in flag
        assert "reason" in flag
        assert "source" in flag


def test_delay_stats_has_source_in_anomalies():
    os.environ["TRANSITSENSE_DB"] = DB
    result = get_delay_stats("219", ("2026-06-01", "2026-06-30"))
    for flag in result["anomaly_flags"]:
        assert flag["source"] in ("synthetic", "real", "unknown")
