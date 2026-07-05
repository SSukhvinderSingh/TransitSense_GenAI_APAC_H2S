# dependencies.md
# Format version: 1.1
# Last updated: 2026-07-05
# Owner: Shawn

## Purpose
Matrix of dependencies across agents/skills and global MasterSkill versions, to prevent version collisions during integration.

## Library Dependencies

| Component | Library | Version (pin when known) | Notes |
|---|---|---|---|
| Data Ingestion Agent | pandas | latest stable | CSV parsing, validation |
| Data Ingestion Agent | sqlite3 | stdlib | local datastore |
| Delay Analysis Skill | pandas, numpy | latest stable | pure deterministic computation |
| Congestion Forecast Skill | pandas, numpy | latest stable | moving average baseline |
| Congestion Forecast Skill | scikit-learn or statsmodels | latest stable | optional, only if linear regression used over moving average |
| Priority Scoring Skill | pandas, numpy | latest stable | consumes Delay Analysis Skill output |
| NL Query Router Skill | google-genai (Gemini SDK) | latest stable | intent/entity extraction only |
| TransitSense Orchestrator | google-genai (Gemini SDK) | latest stable | narration only, never computation |
| TransitSense Orchestrator | fastapi (or plain CLI) | latest stable | optional, for HTTP interface |

## Agent → Skill Dependency Matrix

| Agent/Skill | Depends On |
|---|---|
| TransitSense Orchestrator | NL Query Router Skill, Delay Analysis Skill, Congestion Forecast Skill, Priority Scoring Skill |
| NL Query Router Skill | Gemini API |
| Delay Analysis Skill | Data Ingestion Agent output (transitsense.db) |
| Congestion Forecast Skill | Data Ingestion Agent output (transitsense.db) |
| Priority Scoring Skill | Delay Analysis Skill output, Data Ingestion Agent output |
| Data Ingestion Agent | none (raw CSVs only) |

## MasterSkills

None in use for this project (v0.1.0). Tracked pointer index (currently empty) lives in `masterskills-index.md`. If a reusable MasterSkill is later imported (e.g. a shared NL-parsing utility), record it there with:
- MasterSkill name and version
- Artifact URI
- Required permissions
- License/provenance

Per project instructions, MasterSkills are never committed to this repository — reference by artifact URI only, and add `MasterSkills/` to `.gitignore`.

## External Services

| Service | Used By | Purpose | Secret Handling |
|---|---|---|---|
| Gemini API | NL Query Router Skill, TransitSense Orchestrator | NL parsing + narration only | API key via environment variable, never committed, never logged |

## External Data Sources

| Source | Used For | Access | Provenance Notes |
|---|---|---|---|
| OpenCity open data portal (`data.opencity.in`) | `stops.csv` (real, already staged), TGSRTC GTFS zip (routes/trips/stop_times/calendar — pending local pull) | Free, no signup, direct download | Original data from TSRTC; attribute source per portal terms. Full details in `data_sources.md`. |
| HMRL (Hyderabad Metro Rail) open data | Optional metro GTFS if metro is added to scope | Free, requires email form submission | Attribution required: "Contains data provided by Hyderabad Metro Rail Ltd." per HMRL terms of use. |
| Synthetic generator (in-repo script, not yet built) | `trips_delays.csv`, `ridership.csv` | N/A — generated locally, seeded | Must be tagged `_source: synthetic` per Data Ingestion Agent Enforcement in `agents.md`; never presented as observed fact. |

Full source list, licensing notes, and the explicitly-avoided unofficial scraped ETA API are documented in `data_sources.md` — not duplicated here to avoid drift between the two files.

## Version Collision Notes
Data Ingestion Agent and TransitSense Orchestrator bumped to v0.1.1 on 2026-07-05 (data-provenance Enforcement additions). All other components remain at v0.1.0. Update this table on every Version bump recorded in agents.md/skills.md.
