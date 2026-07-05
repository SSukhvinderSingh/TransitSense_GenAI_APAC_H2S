# skills.md
# Format version: 1.1
# Last updated: 2026-07-05
# Owner: Shawn

## Skill: Delay Analysis Skill

**Role**: Computes deterministic on-time performance and delay statistics per route/stop for a given time window.

**Intent**: Provide ground-truth delay metrics with zero interpretive drift. Success criteria: output matches manually verified test fixture values exactly (floating-point tolerance 1e-6).

**Context**: Reads from `transitsense.db` (populated by Data Ingestion Agent). Assumes ingestion has already run. Pure computation — no network calls.

**Enforcement**:
- No LLM calls inside this skill, ever.
- Latency budget: < 200ms per query on sample dataset.
- Must return raw numeric output plus metadata (row count used, date range actually covered) — never rounded or "interpreted" text.
- Must flag `insufficient_data: true` if fewer than 5 trip records exist for the requested window, rather than returning a misleadingly precise stat.

**Interface**:
```
get_delay_stats(route_id: str, date_range: [str, str]) -> {
  avg_delay_min: float,
  on_time_pct: float,
  anomaly_flags: [ {trip_id: str, delay_min: float, reason: str} ],
  row_count: int,
  insufficient_data: bool
}
```

**Dependencies**: pandas, numpy

**Metadata**: language: python; runtime: 3.11; compatibility: OpenCode, Antigravity, Windsurf; tags: analytics, delay, deterministic

**Version**: 0.1.0

**Changelog**:
- 2026-07-05: Initial draft (Shawn, via Claude planning)

**Test Cases**: `tests/test_delay_skill.py` — known-input/known-output fixtures, anomaly-threshold edge cases, insufficient-data flag check.

**Artifact Location**: `artifact://transitsense/skills/delay_analysis/staging`

---

## Skill: Congestion Forecast Skill

**Role**: Forecasts near-term ridership/delay trend using a deterministic statistical model (moving average or simple linear regression — no LLM).

**Intent**: Give a short-horizon forecast to support planning decisions. Success criteria: MAE on holdout test fixtures within the tolerance defined in test cases; forecast reproducible given identical inputs.

**Context**: Reads historical ridership/delay series from `transitsense.db`. Model choice and parameters are fixed and version-controlled here, not learned ad hoc per query.

**Enforcement**:
- Model type and `model_version` must be logged in every response.
- No LLM involvement in the numeric computation.
- Must flag `low_confidence: true` when fewer than `min_data_points` (default: 14) historical points exist for the series.

**Interface**:
```
forecast_metric(route_id: str, metric: "delay"|"ridership", horizon_days: int) -> {
  forecast: [ {date: str, value: float} ],
  confidence: "high"|"low",
  model_version: str,
  low_confidence: bool
}
```

**Dependencies**: pandas, numpy (statsmodels or scikit-learn optional, only if regression is used over simple moving average)

**Metadata**: language: python; runtime: 3.11; compatibility: OpenCode, Antigravity, Windsurf; tags: analytics, forecasting, deterministic

**Version**: 0.1.0

**Changelog**:
- 2026-07-05: Initial draft (Shawn, via Claude planning)

**Test Cases**: `tests/test_forecast_skill.py` — fixture series with known forecast output, low-confidence flag trigger.

**Artifact Location**: `artifact://transitsense/skills/forecast/staging`

---

## Skill: Priority Scoring Skill

**Role**: Ranks routes/stops by a composite impact score combining delay severity and ridership volume, to surface the highest-impact issues for city planners.

**Intent**: Turn raw metrics into an actionable, defensible priority order. Success criteria: scoring formula is documented, version-controlled, and fully reproducible given the same inputs (no randomness).

**Context**: Consumes output of the Delay Analysis Skill plus ridership counts from `transitsense.db`. Composite formula (v0.1.0): `score = (avg_delay_min * on_time_deficit) * log(1 + ridership)`, where `on_time_deficit = 1 - on_time_pct`.

**Enforcement**:
- Scoring formula changes require a Version bump + Changelog entry — a silent formula change is a hard failure.
- No LLM involvement in score computation.
- Output must include `contributing_factors` so the narration layer (and the human reviewer) can audit *why* a route ranked where it did.

**Interface**:
```
score_routes(date_range: [str, str]) -> [
  { route_id: str, score: float, rank: int, contributing_factors: {avg_delay_min: float, on_time_pct: float, ridership: int} }
]
```

**Dependencies**: Delay Analysis Skill output, ridership table in `transitsense.db`

**Metadata**: language: python; runtime: 3.11; compatibility: OpenCode, Antigravity, Windsurf; tags: analytics, prioritization, deterministic

**Version**: 0.1.0

**Changelog**:
- 2026-07-05: Initial draft (Shawn, via Claude planning)

**Test Cases**: `tests/test_priority_skill.py` — formula regression test against fixed fixture, rank stability check.

**Artifact Location**: `artifact://transitsense/skills/priority_scoring/staging`

---

## Skill: NL Query Router Skill

**Role**: Parses a natural-language question into a structured skill-call specification (target skill, route, metric, date range).

**Intent**: Correctly map free text to skill parameters so the Orchestrator can call deterministic skills. Success criteria: ≥ 0.90 parse accuracy on the labeled test query set.

**Context**: Uses the Gemini API for intent and entity extraction only. Runs before any deterministic skill is invoked.

**Enforcement**:
- MUST return only structured parameters — never a numeric value, never narrative text.
- Any output containing a bare number (other than a route/stop ID) is a validation failure and must be rejected by the Orchestrator before a skill is called.
- Must return `confidence` and set `target_skill: "clarify"` when the query is ambiguous (e.g. no route specified), triggering a clarifying question instead of a guess.

**Interface**:
```
parse_query(text: str) -> {
  target_skill: "delay_analysis"|"forecast"|"priority_scoring"|"clarify",
  route_id: str | null,
  metric: str | null,
  date_range: [str, str] | null,
  confidence: float
}
```

**Dependencies**: Gemini API

**Metadata**: language: python; runtime: 3.11; compatibility: OpenCode, Antigravity, Windsurf; tags: nlp, routing, gemini

**Version**: 0.1.0

**Changelog**:
- 2026-07-05: Initial draft (Shawn, via Claude planning)

**Test Cases**: `tests/test_query_router.py` — labeled query fixtures (~30 sample questions), ambiguous-query clarify-path test, bare-number rejection test.

**Artifact Location**: `artifact://transitsense/skills/query_router/staging`
