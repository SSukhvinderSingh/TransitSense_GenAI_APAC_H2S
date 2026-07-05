# data_sources.md
# Free data sources for TransitSense
# Last updated: 2026-07-05

## What's already pulled (real data, no signup)

**`data/raw/stops.csv`** — real Hyderabad TSRTC bus stop data (stop_id, stop_name, zone_id, stop_lat, stop_lon, stop_desc), pulled directly from OpenCity's open data portal. Source dataset: https://data.opencity.in/dataset/hyderabad-bus-stops (original data from TSRTC). This is a truncated sample (~130 of several hundred stops) to keep the repo small — see "Getting the rest" below if you want the full set.

## Free, no-signup sources

| Source | What it gives you | Access |
|---|---|---|
| OpenCity Hyderabad Bus Stops | Stop ID, name, zone, lat/lon | Direct CSV download, no auth: https://data.opencity.in/dataset/hyderabad-bus-stops |
| OpenCity **TGSRTC Buses GTFS** | Full GTFS zip (routes, stops, trips, calendar) — dated 8 Feb 2026, so it's current | Direct ZIP download, no auth: `https://data.opencity.in/dataset/88e2d145-7ec6-4666-88dd-6cf18b18312e/resource/1b0d18bb-b2fb-4a79-8ed0-1e071da5790c/download/telangana_opendata_gtfs_tgsrtc_08_february_2026.zip` |
| Telangana Open Data Portal | GTFS collections for Hyderabad transit systems | https://data.telangana.gov.in/collection/general-transit-feed-specification-gtfs-hyderabad |
| Mobility Database | 6,000+ GTFS/GTFS-RT/GBFS feeds worldwide, if you want a cleaner feed from elsewhere for comparison | https://mobilitydatabase.org/feeds |

## Free, but needs a quick signup (still no cost)

| Source | What it gives you | Access |
|---|---|---|
| HMRL (Hyderabad Metro Rail) | Official GTFS for Green/Red/Blue metro lines (routes, stops, schedules, fares) | Fill a short form with your email to get the download link: https://hmrl.co.in/open-data/ |

## What's NOT available for free, and what we do instead

No source publishes free per-trip **delay logs** or **ridership counts** for Hyderabad buses — TSRTC has not released this operational data publicly (confirmed via the Telangana Open Data community discussion threads). So:

- `trips_delays.csv` and `ridership.csv` will be **synthesized** on top of the real schedule (real stops/routes + simulated delay and ridership numbers, seeded and documented — not claimed as real).
- This is already reflected as an assumption in `README.md`.

## Explicitly avoided

There's a community-maintained unofficial TSRTC bus ETA API (scraped from the agency's tracking backend, not an authorized public API). The repo maintainer's own README warns it may violate provisions of India's IT Act and recommends consulting a lawyer before use. **Not used or recommended here** — it's not an authorized data source, and legal risk isn't worth it for a hackathon demo. If TSRTC ever publishes an authorized real-time GTFS-RT feed, swap it in here instead.

## Getting the rest of the GTFS zip

The zip URL above (`telangana_opendata_gtfs_tgsrtc_08_february_2026.zip`) isn't reachable from this sandboxed environment (its domain isn't in the allowed egress list here), but it's a direct, no-auth download — pull it locally or from OpenCode's environment with:

```bash
curl -L -o data/raw/tgsrtc_gtfs.zip "https://data.opencity.in/dataset/88e2d145-7ec6-4666-88dd-6cf18b18312e/resource/1b0d18bb-b2fb-4a79-8ed0-1e071da5790c/download/telangana_opendata_gtfs_tgsrtc_08_february_2026.zip"
unzip data/raw/tgsrtc_gtfs.zip -d data/raw/tgsrtc_gtfs/
```

That gives you real `routes.txt`, `trips.txt`, `stop_times.txt`, and `calendar.txt` to replace/extend the `stops.csv` sample already in this repo.
