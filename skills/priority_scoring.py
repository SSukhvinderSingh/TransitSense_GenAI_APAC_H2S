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

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transitsense.db")


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

    route_rows = conn.execute(
        "SELECT DISTINCT t.route_id FROM trips_delays t "
        "INNER JOIN ridership r ON t.route_id = r.route_id"
    ).fetchall()

    dr = date_range or ("2026-06-01", "2026-06-30")
    start_date, end_date = dr

    scored = []
    for rr in route_rows:
        rid = rr["route_id"]

        row = conn.execute(
            "SELECT AVG(delay_minutes) as avg_delay, COUNT(*) as row_count "
            "FROM trips_delays WHERE route_id = ? AND delay_minutes IS NOT NULL "
            "AND date >= ? AND date <= ?",
            (rid, start_date, end_date),
        ).fetchone()

        if not row or row["row_count"] is None or row["row_count"] < 5:
            continue

        avg_delay = round(row["avg_delay"], 2) if row["avg_delay"] else 0
        row_count = row["row_count"]

        on_time = conn.execute(
            "SELECT COUNT(*) as cnt FROM trips_delays "
            "WHERE route_id = ? AND ABS(delay_minutes) <= 5 "
            "AND date >= ? AND date <= ?",
            (rid, start_date, end_date),
        ).fetchone()["cnt"]

        on_time_pct = round((on_time / row_count) * 100, 2)
        on_time_deficit = max(0.0, 1.0 - (on_time_pct / 100.0))

        ridership_row = conn.execute(
            "SELECT SUM(ridership_count) as total FROM ridership WHERE route_id = ?",
            (rid,),
        ).fetchone()
        ridership = ridership_row["total"] if ridership_row and ridership_row["total"] else 0

        if on_time_deficit == 0 or avg_delay == 0:
            continue

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

    conn.close()

    scored.sort(key=lambda x: -x["score"])
    for i, s in enumerate(scored):
        s["rank"] = i + 1

    return scored[:limit]
