#!/usr/bin/env python3
"""
TransitSense Locality Status Skill.
Given a zone/locality name, finds routes serving that area
and returns per-route delay stats with solution suggestions.
"""
import sqlite3
import os
import math

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transitsense.db")


def find_zones(query=None):
    """
    Return list of zone names matching query, or popular zones if no query.
    """
    db_path = os.environ.get("TRANSITSENSE_DB", DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    if query:
        zones = conn.execute(
            "SELECT DISTINCT s.zone_id, COUNT(DISTINCT td.route_id) as route_count "
            "FROM trips_delays td JOIN stops s ON td.stop_id = s.stop_id "
            "WHERE s.zone_id LIKE ? AND s.zone_id != '' "
            "GROUP BY s.zone_id ORDER BY route_count DESC LIMIT 10",
            (f"%{query}%",),
        ).fetchall()
    else:
        zones = conn.execute(
            "SELECT s.zone_id, COUNT(DISTINCT td.route_id) as route_count "
            "FROM trips_delays td JOIN stops s ON td.stop_id = s.stop_id "
            "WHERE s.zone_id != '' "
            "GROUP BY s.zone_id ORDER BY route_count DESC LIMIT 8"
        ).fetchall()

    conn.close()
    return [{"name": z["zone_id"], "routes": z["route_count"]} for z in zones]


def _generate_solutions(route_stats):
    """Generate solution suggestions for each route based on its stats."""
    solutions = []
    for r in route_stats:
        advice = []
        if r["on_time_pct"] < 60:
            advice.append("increase schedule buffer by 2-3 min during peak hours")
        if r["avg_delay_min"] > 10:
            advice.append("investigate traffic congestion patterns along this corridor")
        if r["anomaly_count"] > 50:
            advice.append("review trip scheduling — high anomaly rate suggests inconsistent performance")
        if r["ridership"] > 50000 and r["on_time_pct"] < 70:
            advice.append("consider adding frequency during high-demand periods")
        if r["ridership"] < 10000 and r["on_time_pct"] > 85:
            advice.append("route performance is good — maintain current schedule")

        if advice:
            solutions.append({
                "route_id": r["route_id"],
                "issues": advice,
            })
    return solutions


def get_locality_status(zone_name, date_range=None):
    """
    Get delay stats for all routes serving a given zone/locality.

    Args:
        zone_name: Locality/zone name to look up.
        date_range: Optional (start_date, end_date).

    Returns:
        dict with zone info, route statuses, and solutions.
    """
    db_path = os.environ.get("TRANSITSENSE_DB", DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Find routes serving stops in this zone
    query = """
        SELECT DISTINCT td.route_id, s.zone_id
        FROM trips_delays td
        JOIN stops s ON td.stop_id = s.stop_id
        WHERE s.zone_id = ? COLLATE NOCASE
    """
    params = [zone_name]

    route_rows = conn.execute(query, params).fetchall()
    route_ids = list(set(r["route_id"] for r in route_rows))

    if not route_ids:
        conn.close()
        return {
            "zone": zone_name,
            "route_statuses": [],
            "solutions": [],
            "found": False,
            "total_routes": 0,
        }

    # Compute aggregate stats per route
    date_filter = ""
    date_params = []
    if date_range:
        date_filter = " AND td.date >= ? AND td.date <= ?"
        date_params = [date_range[0], date_range[1]]

    route_stats = []
    for rid in route_ids:
        params_list = [rid] + date_params
        row = conn.execute(
            f"SELECT AVG(td.delay_minutes) as avg_delay, COUNT(*) as row_count "
            f"FROM trips_delays td JOIN stops s ON td.stop_id = s.stop_id "
            f"WHERE td.route_id = ? AND s.zone_id = ? COLLATE NOCASE{date_filter}",
            [rid, zone_name] + date_params,
        ).fetchone()

        if not row or row["row_count"] == 0:
            continue

        avg_delay = round(row["avg_delay"], 2) if row["avg_delay"] else 0
        row_count = row["row_count"]

        # On-time percentage (abs(delay) <= 5 min)
        on_time = conn.execute(
            f"SELECT COUNT(*) as cnt FROM trips_delays td "
            f"JOIN stops s ON td.stop_id = s.stop_id "
            f"WHERE td.route_id = ? AND s.zone_id = ? COLLATE NOCASE "
            f"AND ABS(td.delay_minutes) <= 5{date_filter}",
            [rid, zone_name] + date_params,
        ).fetchone()

        on_time_pct = round((on_time["cnt"] / row_count) * 100, 2) if row_count else 0

        # Anomaly count
        anomaly = conn.execute(
            f"SELECT COUNT(*) as cnt FROM trips_delays td "
            f"JOIN stops s ON td.stop_id = s.stop_id "
            f"WHERE td.route_id = ? AND s.zone_id = ? COLLATE NOCASE "
            f"AND (td.delay_minutes > 15 OR td.delay_minutes < -5){date_filter}",
            [rid, zone_name] + date_params,
        ).fetchone()

        # Ridership from ridership table
        ridership_row = conn.execute(
            "SELECT SUM(ridership_count) as total FROM ridership WHERE route_id = ?",
            (rid,),
        ).fetchone()
        ridership = ridership_row["total"] if ridership_row and ridership_row["total"] else 0

        route_stats.append({
            "route_id": rid,
            "avg_delay_min": avg_delay,
            "on_time_pct": on_time_pct,
            "anomaly_count": anomaly["cnt"] if anomaly else 0,
            "row_count": row_count,
            "ridership": ridership,
        })

    route_stats.sort(key=lambda x: -x["avg_delay_min"])

    # Generate solutions
    solutions = _generate_solutions(route_stats)

    conn.close()

    return {
        "zone": zone_name,
        "route_statuses": route_stats,
        "solutions": solutions,
        "found": True,
        "total_routes": len(route_stats),
    }
