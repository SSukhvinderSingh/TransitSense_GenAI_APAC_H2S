#!/usr/bin/env python3
"""
TransitSense Congestion Forecast Skill.
Deterministic moving-average forecast for delay or ridership.
Model: ma_v0.1.0 (7-day simple moving average).
No LLM calls.
"""
import sqlite3
import os
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transitsense.db")
MOVING_AVERAGE_WINDOW = 7
MIN_DATA_POINTS = 14
MODEL_VERSION = "ma_v0.1.0"


def _load_daily_delays(conn, route_id):
    rows = conn.execute(
        "SELECT date, AVG(delay_minutes) as avg_delay FROM trips_delays "
        "WHERE route_id = ? AND delay_minutes IS NOT NULL "
        "GROUP BY date ORDER BY date",
        (route_id,),
    ).fetchall()
    return [(r["date"], r["avg_delay"]) for r in rows]


def _load_daily_ridership(conn, route_id):
    rows = conn.execute(
        "SELECT date, SUM(ridership_count) as total FROM ridership "
        "WHERE route_id = ? AND ridership_count IS NOT NULL "
        "GROUP BY date ORDER BY date",
        (route_id,),
    ).fetchall()
    return [(r["date"], r["total"]) for r in rows]


def _moving_average_forecast(series, horizon_days):
    """Simple moving average forecast."""
    if len(series) < MIN_DATA_POINTS:
        return [], "low", True

    values = [v for _, v in series]
    window = min(MOVING_AVERAGE_WINDOW, len(values))

    # Compute moving average on last window points
    recent_avg = sum(values[-window:]) / window

    # Generate forecast dates starting from last date + 1 day
    from datetime import datetime, timedelta
    last_date = datetime.strptime(series[-1][0], "%Y-%m-%d")
    confidence = "high"

    forecast = []
    for i in range(1, horizon_days + 1):
        forecast_date = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
        forecast.append({
            "date": forecast_date,
            "value": round(recent_avg + (i * 0.1), 2),
        })

    return forecast, confidence, False


def forecast_metric(route_id, metric="delay", horizon_days=7):
    """
    Forecast a metric for a given route.

    Args:
        route_id: Route identifier.
        metric: "delay" or "ridership".
        horizon_days: Number of days to forecast.

    Returns:
        dict with forecast, confidence, model_version, low_confidence.
    """
    db_path = os.environ.get("TRANSITSENSE_DB", DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    if metric == "delay":
        series = _load_daily_delays(conn, route_id)
    elif metric == "ridership":
        series = _load_daily_ridership(conn, route_id)
    else:
        conn.close()
        return {
            "forecast": [],
            "confidence": "low",
            "model_version": MODEL_VERSION,
            "low_confidence": True,
            "error": f"Unknown metric: {metric}",
        }

    conn.close()

    forecast, confidence, low_confidence = _moving_average_forecast(series, horizon_days)

    return {
        "forecast": forecast,
        "confidence": confidence,
        "model_version": MODEL_VERSION,
        "low_confidence": low_confidence,
        "route_id": route_id,
        "metric": metric,
    }
