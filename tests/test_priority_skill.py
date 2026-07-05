#!/usr/bin/env python3
"""Tests for Priority Scoring Skill."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skills.priority_scoring import score_routes

DB = os.path.join(os.path.dirname(__file__), "..", "data", "transitsense.db")


def test_score_routes_returns_ranked():
    os.environ["TRANSITSENSE_DB"] = DB
    results = score_routes(("2026-06-01", "2026-06-30"), 5)
    assert len(results) == 5
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    for r in results:
        assert r["rank"] >= 1
        assert "contributing_factors" in r
        assert "avg_delay_min" in r["contributing_factors"]
        assert "on_time_pct" in r["contributing_factors"]
        assert "ridership" in r["contributing_factors"]


def test_score_routes_no_duplicate_ranks():
    os.environ["TRANSITSENSE_DB"] = DB
    results = score_routes(("2026-06-01", "2026-06-30"), 20)
    ranks = [r["rank"] for r in results]
    assert len(ranks) == len(set(ranks))
