#!/usr/bin/env python3
"""
TransitSense Priority Scoring Skill.
Ranks routes by composite impact score.
Formula (v0.1.0): score = (avg_delay_min * on_time_deficit) * log(1 + ridership)
No LLM calls.
"""
import math
import sqlite3
import os

from skills.delay_analysis import get_delay_stats

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transitsense.db")


def _get_ridership_for_route(conn, route_id, date_range):
    start_date, end_date = date_range
    row = conn.execute(
        "SELECT SUM(ridership_count) as total FROM ridership "
        "WHERE route_id = ? AND date >= ? AND date <= ?",
        (route_id, start_date, end_date),
    ).fetchone()
    return row["total"] if row and row["total"] else 0


def score_routes(date_range=None, limit=20):
    """
    Rank all routes by composite impact score.

    Args:
        date_range: Optional (start_date, end_date) ISO strings.
        limit: Max number of routes to return.

    Returns:
        List of dicts sorted by score descending.
    """
    db_path = os.environ.get("TRANSITSENSE_DB", DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    route_rows = conn.execute("SELECT route_id FROM routes").fetchall()
    conn.close()

    scored = []
    for rr in route_rows:
        rid = rr["route_id"]
        stats = get_delay_stats(rid, date_range)

        if stats["insufficient_data"]:
            continue

        avg_delay = stats["avg_delay_min"]
        on_time_pct = stats["on_time_pct"]
        on_time_deficit = max(0.0, 1.0 - (on_time_pct / 100.0))

        if on_time_deficit == 0 or avg_delay == 0:
            continue

        conn2 = sqlite3.connect(db_path)
        conn2.row_factory = sqlite3.Row
        ridership = _get_ridership_for_route(conn2, rid, date_range or ("2026-06-01", "2026-06-30"))
        conn2.close()

        score = round((avg_delay * on_time_deficit) * math.log10(1 + max(ridership, 0)), 4)

        scored.append({
            "route_id": rid,
            "score": score,
            "rank": 0,
            "contributing_factors": {
                "avg_delay_min": avg_delay,
                "on_time_pct": on_time_pct,
                "ridership": ridership,
            },
        })

    scored.sort(key=lambda x: -x["score"])
    for i, s in enumerate(scored):
        s["rank"] = i + 1

    return scored[:limit]
