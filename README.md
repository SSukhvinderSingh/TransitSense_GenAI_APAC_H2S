# TransitSense

**An AI-powered Decision Intelligence copilot for urban transit — turning route delay, ridership, and schedule data into explainable insights, forecasts, and recommendations for city planners and commuters.**

## Chosen Vertical
Urban mobility and transportation, within the broader "AI-powered Decision Intelligence Platform" challenge.

## Problem
City transit systems generate delay logs, ridership counts, and schedule data every day, but turning that into an answerable, trustworthy "why is this route always late, and what should we do about it" is hard. Most quick solutions either bury planners in raw dashboards or hand the numbers to an LLM and hope it doesn't hallucinate a statistic.

## Approach & Logic
TransitSense is built deterministic-first, LLM-second:

1. **Data Ingestion Agent** loads raw route/stop/delay/ridership CSVs into a local SQLite store, validating schema and logging (never silently dropping) any bad rows.
2. **Three deterministic skills** — Delay Analysis, Congestion Forecast, and Priority Scoring — do all the actual math (averages, on-time percentages, anomaly detection, short-horizon forecasts, composite impact scores). These are plain Python/pandas/numpy, unit-tested against fixed fixtures, and contain **no LLM calls**.
3. **NL Query Router Skill** uses Gemini only to turn a free-text question ("why is Route 12 always late on Fridays?") into structured parameters (route, metric, date range) that get handed to the right deterministic skill.
4. **TransitSense Orchestrator** calls the right skill, then asks Gemini to narrate the *skill's own output* in plain language and suggest a recommendation — never to compute a number itself. Every numeric value in a response must trace back verbatim to a skill call, or the response is rejected before it reaches the user.

This mirrors the RICE/CRAFT structure in `agents.md`, `skills.md`, and `progress.md`: agents/skills are static, versioned RICE specs, and `progress.md` is the living CRAFT ledger tracking implementation status, test runs, and manual verification.

## How It Works (end to end)
```
raw CSVs → Data Ingestion Agent → transitsense.db
                                        ↓
user question → NL Query Router Skill (Gemini: parse only)
                                        ↓
              → Delay Analysis / Forecast / Priority Scoring Skill (deterministic)
                                        ↓
              → TransitSense Orchestrator → Gemini (narrate only) → answer to user
```

## Assumptions
- Stop-level schedule data (`stops.csv`) is **real** Hyderabad TSRTC data, sourced directly from OpenCity's open data portal (free, no signup). Route/trip/stop_times data is intended to come from the same portal's TGSRTC GTFS feed. Delay and ridership logs are **synthesized** on top of the real schedule, since no free source publishes that operational data for Hyderabad — every synthetic row is tagged `_source: synthetic` so skills and narration never present it as an observed fact. Full provenance is in `data_sources.md`.
- No live/real-time GTFS-RT integration was in scope given hackathon time constraints.
- A single Gemini API key is used for both NL parsing and narration calls; no other Google Cloud services (Vertex AI, BigQuery, etc.) are required to demonstrate the core decision-intelligence loop, though the architecture's clean agent/skill interfaces would allow swapping in those services later.
- All numeric outputs are computed by deterministic Python code, not the LLM, by design — this is treated as a hard, non-negotiable constraint (see Enforcement sections in `agents.md`/`skills.md`), not just a best practice.
- Repository is public, single-branch, and kept under the 10MB limit by using a small curated sample dataset rather than a full historical dump.

## Repository Structure
```
/agents.md              - RICE-structured agent definitions
/skills.md              - RICE-structured skill definitions
/progress.md            - living CRAFT ledger
/dependencies.md        - dependency matrix
/data_sources.md        - free data source list, provenance, what's real vs synthetic
/masterskills-index.md  - tracked pointer index for MasterSkills (currently empty)
/data/raw/              - CSVs: stops.csv (real, staged), routes/trips_delays/ridership (pending)
/tests/                 - unit + integration tests per agent/skill
.gitignore
```

## Manual Verification
Per project instructions, no agent commits automatically. All builds/tests are published as artifacts and marked "Awaiting Verification" in `progress.md` until a human reviewer approves.

> **Note:** AI response may be rate limited due to free tier.
