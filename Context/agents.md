# agents.md
# Format version: 1.1
# Last updated: 2026-07-05
# Owner: Shawn

## Agent: TransitSense Orchestrator

**Role**: Single owner of conversational orchestration — receives natural-language questions/commands about transit performance from citizens or city planners, routes them to the correct deterministic skill(s), and requests Gemini narration of the returned results.

**Intent**: Enable accurate, explainable natural-language Q&A over transit KPI data. Success criteria:
- 100% of numeric values in any response trace back verbatim to a skill output (zero LLM-fabricated numbers).
- Intent/route classification accuracy ≥ 0.90 on the labeled test query set (see NL Query Router Skill test cases).
- End-to-end response latency < 4s on sample dataset.

**Context**: Runs as a Python service (FastAPI or CLI wrapper for hackathon scope). Consumes the normalized SQLite datastore produced by the Data Ingestion Agent. Uses the Gemini API exclusively for natural-language understanding (via NL Query Router Skill) and final narration — never for arithmetic. Sample data scope: Hyderabad-style bus route schedules, delay logs, and ridership counts.

**Enforcement**:
- MUST NOT compute, estimate, or restate a numeric metric (delay minutes, percentages, forecasts, scores) except by passing through a skill's exact output.
- Every Gemini call for narration MUST include the raw skill output JSON in-context and MUST NOT be asked to "calculate" anything.
- Token budget: max 2,000 tokens per Gemini call.
- Must redact API keys / secrets from all logs written to `progress.md` or artifact store.
- Any response where a bare number cannot be traced to a skill call must be rejected before returning to the user (validation gate).
- Must surface data provenance in every narrated answer: if any figure used derives from a row tagged `_source: synthetic` (see Data Ingestion Agent), the response text must say so plainly (e.g. "based on simulated ridership data") rather than presenting it as an observed fact.

**Inputs**: `{query: string, session_id: string, conversation_history?: array}`

**Outputs**: `{answer_text: string, cited_metrics: object, source_skill: string, skill_calls: array}`

**Dependencies**: NL Query Router Skill, Delay Analysis Skill, Congestion Forecast Skill, Priority Scoring Skill, Gemini API

**Interface**:
```
POST /query
Request:  { "query": "string", "session_id": "string" }
Response: { "answer_text": "string", "cited_metrics": {}, "source_skill": "string", "skill_calls": [] }
```

**Metadata**: language: python; runtime: 3.11; compatibility: OpenCode, Antigravity, Windsurf; tags: orchestration, nlp, transit, decision-intelligence

**Version**: 0.1.1

**Changelog**:
- 2026-07-05: Initial draft (Shawn, via Claude planning)
- 2026-07-05: Added data-provenance disclosure rule to Enforcement (Shawn, via Claude planning)

**Test Cases**: `tests/test_orchestrator.py` — covers query routing correctness and a "no-fabrication" check that fails the build if any numeric token in a response is absent from the upstream skill output. CI: `pytest tests/test_orchestrator.py`

**Artifact Location**: `artifact://transitsense/orchestrator/staging`

---

## Agent: Data Ingestion Agent

**Role**: Single owner of loading, validating, and normalizing raw transit datasets (schedule, delay logs, ridership) into a queryable local store.

**Intent**: Ensure clean, consistent data is available to all skills before any query is served. Success criteria:
- 0 schema validation failures on the shipped sample dataset.
- Ingestion completes in < 5s for the provided sample size.
- Ingestion report clearly logs any dropped/malformed rows (never silent drops).

**Context**: Reads CSV files from `/data/raw/` (`routes.csv`, `stops.csv`, `trips_delays.csv`, `ridership.csv`). Writes to SQLite at `/data/transitsense.db`. Run once at project setup and on any data refresh. No PII expected in dataset (transit operational data only). `stops.csv` is real Hyderabad TSRTC data sourced from OpenCity's open data portal; `routes.csv`/`trips.csv` are intended to come from the TGSRTC GTFS feed (also OpenCity, see `data_sources.md`); `trips_delays.csv` and `ridership.csv` are synthesized on top of the real schedule since no free source publishes that operational data. Full provenance and source URLs are tracked in `data_sources.md`, not duplicated here.

**Enforcement**:
- Must validate required columns exist before writing; fail fast with a clear error if schema mismatches.
- Must log every dropped or malformed row to `ingestion_report.json` — silent drops are a hard failure.
- Must run a PII scan pass over free-text fields (e.g. any citizen-submitted notes) even though none are expected, and refuse to ingest + log a refusal in `progress.md` if PII is detected.
- Must tag each row's source as `real` or `synthetic` in an added `_source` column so downstream skills and narration can distinguish grounded data from simulated data — this must never be dropped or hidden from the Orchestrator's narration context.

**Inputs**: CSV files under `/data/raw/`

**Outputs**: `transitsense.db` (SQLite), `ingestion_report.json` (row counts, validation errors, dropped rows)

**Dependencies**: pandas, sqlite3 (stdlib)

**Interface**:
```
CLI: python ingest.py --input data/raw --output data/transitsense.db
```

**Metadata**: language: python; runtime: 3.11; compatibility: OpenCode, Antigravity, Windsurf; tags: data, ingestion, etl

**Version**: 0.1.1

**Changelog**:
- 2026-07-05: Initial draft (Shawn, via Claude planning)
- 2026-07-05: Added real/synthetic data provenance to Context; added `_source` column requirement to Enforcement (Shawn, via Claude planning)

**Test Cases**: `tests/test_ingestion.py` — malformed-row detection, schema validation, PII scan, and a `_source` column presence/values check. CI: `pytest tests/test_ingestion.py`

**Artifact Location**: `artifact://transitsense/ingestion/staging`
