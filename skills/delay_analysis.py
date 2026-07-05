#!/usr/bin/env python3
"""
TransitSense Delay Analysis Skill.
Deterministic on-time performance and delay statistics per route.
No LLM calls.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transitsense.db")

ON_TIME_THRESHOLD = 5.0
ANOMALY_LATE_THRESHOLD = 15.0
ANOMALY_EARLY_THRESHOLD = -5.0
MIN_DATA_POINTS = 5


def get_delay_stats(route_id: str, date_range: tuple = None):
    """
    Compute delay statistics for a given route.

    Args:
        route_id: Route identifier.
        date_range: Optional (start_date, end_date) ISO format strings.

    Returns:
        dict with avg_delay_min, on_time_pct, anomaly_flags, row_count,
        insufficient_data, date_range_covered.
    """
    db_path = os.environ.get("TRANSITSENSE_DB", DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = "SELECT trip_id, delay_minutes, date, delay_reason, _source FROM trips_delays WHERE route_id = ?"
    params = [route_id]

    if date_range:
        start_date, end_date = date_range
        query += " AND date >= ? AND date <= ?"
        params.extend([start_date, end_date])

    rows = conn.execute(query, params).fetchall()
    conn.close()

    row_count = len(rows)

    if row_count < MIN_DATA_POINTS:
        return {
            "avg_delay_min": 0.0,
            "on_time_pct": 0.0,
            "anomaly_flags": [],
            "row_count": row_count,
            "insufficient_data": True,
            "date_range_covered": date_range if date_range else None,
            "route_id": route_id,
        }

    delays = [r["delay_minutes"] for r in rows if r["delay_minutes"] is not None]
    if not delays:
        return {
            "avg_delay_min": 0.0,
            "on_time_pct": 0.0,
            "anomaly_flags": [],
            "row_count": row_count,
            "insufficient_data": True,
            "date_range_covered": date_range if date_range else None,
            "route_id": route_id,
        }

    avg_delay_min = round(sum(delays) / len(delays), 2)

    on_time_count = sum(1 for d in delays if abs(d) <= ON_TIME_THRESHOLD)
    on_time_pct = round((on_time_count / len(delays)) * 100, 2)

    anomaly_flags = []
    for r in rows:
        d = r["delay_minutes"]
        if d is None:
            continue
        if d > ANOMALY_LATE_THRESHOLD:
            anomaly_flags.append({
                "trip_id": r["trip_id"],
                "delay_min": d,
                "reason": "severe_delay",
                "source": r["_source"] if r["_source"] else "unknown",
            })
        elif d < ANOMALY_EARLY_THRESHOLD:
            anomaly_flags.append({
                "trip_id": r["trip_id"],
                "delay_min": d,
                "reason": "early_departure",
                "source": r["_source"] if r["_source"] else "unknown",
            })

    # Determine date range covered
    dates = sorted(set(r["date"] for r in rows if r["date"]))
    date_range_covered = [dates[0], dates[-1]] if dates else date_range

    return {
        "avg_delay_min": avg_delay_min,
        "on_time_pct": on_time_pct,
        "anomaly_flags": anomaly_flags[:20],
        "row_count": row_count,
        "insufficient_data": False,
        "date_range_covered": date_range_covered,
        "route_id": route_id,
    }
