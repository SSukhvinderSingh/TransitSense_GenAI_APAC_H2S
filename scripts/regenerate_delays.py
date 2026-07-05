#!/usr/bin/env python3
"""
Regenerate trips_delays.csv with real stop_ids from GTFS stop_times,
so zone→route mapping works for locality status queries.
"""
import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)
RAW = os.path.join("data", "raw")
GTFS = os.path.join(RAW, "tgsrtc_gtfs")

# 1. Build trip_id → [stop_id, ...] mapping from stop_times.txt
print("Loading stop_times...")
trip_stops = {}
with open(os.path.join(GTFS, "stop_times.txt"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        tid = row["trip_id"]
        trip_stops.setdefault(tid, []).append(row["stop_id"])

print(f"Loaded {len(trip_stops)} trips with stops from stop_times")

# 2. Load our existing trips_delays to get the trip_ids in our sample
existing = []
with open(os.path.join(RAW, "trips_delays.csv"), newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        existing.append(row)

print(f"Existing delay rows: {len(existing)}")

# 3. Build a trip_id → route_id lookup from existing data
trip_route = {}
for r in existing:
    trip_route[r["trip_id"]] = r["route_id"]

# 4. Regenerate with real stop_ids
base_date = datetime(2026, 6, 1)
new_rows = []
total_trips = len(set(r["trip_id"] for r in existing))

for t in existing:
    tid = t["trip_id"]
    route_id = t["route_id"]

    # Pick a stop from the real stop_times for this trip
    stops_for_trip = trip_stops.get(tid, [])
    stop_id = random.choice(stops_for_trip) if stops_for_trip else ""

    # Re-generate delay (same as original setup_data.py)
    delay = round(random.gauss(3, 8), 1)
    delay = max(-5, min(45, delay))

    date_str = t["date"]

    new_rows.append({
        "trip_id": tid,
        "route_id": route_id,
        "stop_id": stop_id,
        "date": date_str,
        "scheduled_departure": "08:00:00",
        "actual_departure": f"08:{int(4+delay):02d}:00" if delay >= 0 else f"07:{int(60+delay):02d}:00",
        "delay_minutes": delay,
        "delay_reason": "traffic" if delay > 10 else "weather" if delay > 5 else "",
        "_source": "synthetic",
    })

# 5. Write updated file
with open(os.path.join(RAW, "trips_delays.csv"), "w", newline="", encoding="utf-8") as f:
    fields = ["trip_id","route_id","stop_id","date","scheduled_departure","actual_departure","delay_minutes","delay_reason","_source"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(new_rows)

print(f"Written trips_delays.csv: {len(new_rows)} rows with stop_ids populated")

# 6. Cleanup GTFS extract
import shutil
shutil.rmtree(GTFS, ignore_errors=True)
os.remove(os.path.join(RAW, "tgsrtc_gtfs.zip"))
print("Cleaned up GTFS archive")
