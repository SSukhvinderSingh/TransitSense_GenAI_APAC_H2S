#!/usr/bin/env python3
"""
TransitSense data setup script.
Loads real TGSRTC GTFS data, samples a route subset, and produces:
  data/raw/routes.csv, stops.csv, trips_delays.csv, ridership.csv
"""
import csv
import os
import random
import shutil
from datetime import datetime, timedelta

random.seed(42)

RAW = os.path.join("data", "raw")
GTFS = os.path.join(RAW, "tgsrtc_gtfs")
os.makedirs(RAW, exist_ok=True)

# ── 1. Copy real stops.csv (already staged by user) ──
# Already present at data/raw/stops.csv, nothing to do.

# ── 2. Copy all routes (only 21KB) ──
shutil.copy2(os.path.join(GTFS, "routes.txt"), os.path.join(RAW, "routes.csv"))
print("Copied routes.csv (all 1031 routes)")

# ── 3. Load stops from user's staged file ──
with open(os.path.join(RAW, "stops.csv"), newline="", encoding="utf-8") as f:
    stop_ids = {row["stop_id"] for row in csv.DictReader(f)}
print(f"Loaded {len(stop_ids)} stops from staged stops.csv")

# ── 4. Load trips and filter to a subset of routes ──
with open(os.path.join(GTFS, "trips.txt"), newline="", encoding="utf-8") as f:
    trips = list(csv.DictReader(f))

route_trips = {}
for t in trips:
    route_trips.setdefault(t["route_id"], []).append(t)

# Pick 20 routes that have at least 10 trips each
candidates = [(rid, ts) for rid, ts in route_trips.items() if len(ts) >= 10]
candidates.sort(key=lambda x: -len(x[1]))
selected_routes = dict(candidates[:20])

route_ids = set(selected_routes.keys())
selected_trip_ids = set()
for ts in selected_routes.values():
    for t in ts:
        selected_trip_ids.add(t["trip_id"])
print(f"Sampled {len(route_ids)} routes with {len(selected_trip_ids)} trips")

# Write filtered trips to a reference file (used by synthesis below)
sampled_trips = [t for t in trips if t["trip_id"] in selected_trip_ids]
print(f"Sampled trips: {len(sampled_trips)}")

# ── 5. Filter stop_times for selected trips and collect all stop_ids used ──
stop_times_subset = []
used_stop_ids = set()
with open(os.path.join(GTFS, "stop_times.txt"), newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["trip_id"] in selected_trip_ids:
            stop_times_subset.append(row)
            used_stop_ids.add(row["stop_id"])
print(f"Sampled stop_times: {len(stop_times_subset)}, unique stops used: {len(used_stop_ids)}")

# Merge used stops with our staged stops and write full stops.csv
all_stops = dict()
with open(os.path.join(GTFS, "stops.txt"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["stop_id"] in used_stop_ids or row["stop_id"] in stop_ids:
            all_stops[row["stop_id"]] = row
print(f"Writing stops.csv with {len(all_stops)} stops")

with open(os.path.join(RAW, "stops.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["stop_id","stop_name","zone_id","stop_lat","stop_lon","stop_desc"])
    writer.writeheader()
    writer.writerows(all_stops.values())

# Add used stops that weren't in our staged set to the stop_ids for consistency
stop_ids.update(used_stop_ids)

# ── 6. Synthesize trips_delays.csv ──
# Generate delay records for each trip over the last 30 days
base_date = datetime(2026, 6, 1)
routes_lookup = {}
with open(os.path.join(RAW, "routes.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        routes_lookup[row["route_id"]] = row["route_long_name"]

delay_rows = []
for t in sampled_trips:
    for day_offset in range(30):
        date = base_date + timedelta(days=day_offset)
        # Realistic delay distribution: most trips on-time, some late, few very late
        delay = round(random.gauss(3, 8), 1)
        delay = max(-5, min(45, delay))  # clamp between 5min early and 45min late
        delay_rows.append({
            "trip_id": t["trip_id"],
            "route_id": t["route_id"],
            "stop_id": "",
            "date": date.strftime("%Y-%m-%d"),
            "scheduled_departure": "08:00:00",
            "actual_departure": f"08:{int(4+delay):02d}:00" if delay >= 0 else f"07:{int(60+delay):02d}:00",
            "delay_minutes": delay,
            "delay_reason": "traffic" if delay > 10 else "weather" if delay > 5 else "",
            "_source": "synthetic"
        })

with open(os.path.join(RAW, "trips_delays.csv"), "w", newline="", encoding="utf-8") as f:
    fields = ["trip_id","route_id","stop_id","date","scheduled_departure","actual_departure","delay_minutes","delay_reason","_source"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(delay_rows)
print(f"Written trips_delays.csv: {len(delay_rows)} rows")

# ── 7. Synthesize ridership.csv ──
ridership_rows = []
for rid in route_ids:
    for day_offset in range(30):
        date = base_date + timedelta(days=day_offset)
        weekday = date.weekday()
        base_riders = random.randint(800, 5000)
        if weekday >= 5:
            base_riders = int(base_riders * 0.6)
        ridership_rows.append({
            "route_id": rid,
            "date": date.strftime("%Y-%m-%d"),
            "ridership_count": base_riders + random.randint(-200, 200),
            "_source": "synthetic"
        })

with open(os.path.join(RAW, "ridership.csv"), "w", newline="", encoding="utf-8") as f:
    fields = ["route_id","date","ridership_count","_source"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(ridership_rows)
print(f"Written ridership.csv: {len(ridership_rows)} rows")

# ── 8. Remove large GTFS extract to save space ──
shutil.rmtree(os.path.join(RAW, "tgsrtc_gtfs"), ignore_errors=True)
os.remove(os.path.join(RAW, "tgsrtc_gtfs.zip"))
print("Cleaned up GTFS archive. Done.")
