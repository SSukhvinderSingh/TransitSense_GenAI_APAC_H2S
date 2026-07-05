#!/usr/bin/env python3
"""Tests for Congestion Forecast Skill."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skills.congestion_forecast import forecast_metric

DB = os.path.join(os.path.dirname(__file__), "..", "data", "transitsense.db")


def test_forecast_delay():
    os.environ["TRANSITSENSE_DB"] = DB
    result = forecast_metric("219", "delay", 7)
    assert result["route_id"] == "219"
    assert result["metric"] == "delay"
    assert result["model_version"] == "ma_v0.1.0"
    assert len(result["forecast"]) == 7
    for f in result["forecast"]:
        assert "date" in f
        assert "value" in f


def test_forecast_ridership():
    os.environ["TRANSITSENSE_DB"] = DB
    result = forecast_metric("49M", "ridership", 3)
    assert len(result["forecast"]) == 3
    assert result["low_confidence"] is False


def test_forecast_unknown_route():
    os.environ["TRANSITSENSE_DB"] = DB
    result = forecast_metric("NONEXISTENT", "delay", 5)
    assert result["low_confidence"] is True
    assert result["forecast"] == []


def test_forecast_unknown_metric():
    os.environ["TRANSITSENSE_DB"] = DB
    result = forecast_metric("219", "invalid_metric", 3)
    assert "error" in result
