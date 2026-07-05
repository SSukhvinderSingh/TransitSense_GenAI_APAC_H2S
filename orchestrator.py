#!/usr/bin/env python3
"""
TransitSense Orchestrator — FastAPI service.
Routes NL queries → deterministic skills → Gemini narration.
"""
import json
import os
import re
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from skills.query_router import parse_query
from skills.delay_analysis import get_delay_stats
from skills.congestion_forecast import forecast_metric
from skills.priority_scoring import score_routes
from skills.locality_status import get_locality_status, find_zones

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("transitsense")

app = FastAPI(title="TransitSense", version="0.1.0")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Simple in-memory session store for multi-turn conversations
_sessions = {}


def _get_session(session_id):
    if session_id not in _sessions:
        _sessions[session_id] = {
            "awaiting_locality": False,
            "last_skill": None,
            "last_output": None,
            "last_params": None,
        }
    return _sessions[session_id]


class QueryRequest(BaseModel):
    query: str
    session_id: str


class QueryResponse(BaseModel):
    answer_text: str
    cited_metrics: dict
    source_skill: str
    skill_calls: list
    data_provenance: Optional[str] = None


def _extract_numbers(obj):
    """Recursively extract all float/int values from a nested dict/list."""
    nums = set()
    if isinstance(obj, dict):
        for v in obj.values():
            nums.update(_extract_numbers(v))
    elif isinstance(obj, list):
        for item in obj:
            nums.update(_extract_numbers(item))
    elif isinstance(obj, (int, float)):
        nums.add(str(obj))
    return nums


def _check_fabrication(response_text, skill_output):
    """Fail if any number in response text can't be traced to skill output."""
    response_nums = set(re.findall(r"\b\d+\.?\d*\b", response_text))
    skill_nums = _extract_numbers(skill_output)
    for num in response_nums:
        if num not in skill_nums:
            logger.warning(f"Possible fabrication: number '{num}' not in skill output")
            return False
    return True


def _check_synthetic_provenance(skill_output):
    """Check if any synthetic data was used."""
    if isinstance(skill_output, dict):
        for entry in skill_output.get("anomaly_flags", []):
            if entry.get("source") == "synthetic":
                return True
    return False


def _narrate_result(route_params, skill_output, skill_name):
    """Narrate skill output using Gemini, or fall back to template."""
    api_key = os.environ.get("GEMINI_API_KEY", "")

    has_synthetic = _check_synthetic_provenance(skill_output)

    if api_key and api_key != "your_key_here":
        return _narrate_with_gemini(route_params, skill_output, skill_name, api_key, has_synthetic)
    else:
        return _narrate_template(route_params, skill_output, skill_name, has_synthetic)


def _narrate_with_gemini(route_params, skill_output, skill_name, api_key, has_synthetic):
    """Use Gemini to narrate skill output. Falls back to template on error."""
    from google import genai
    from google.genai import errors as genai_errors

    client = genai.Client(api_key=api_key)
    provenance_note = ""
    if has_synthetic:
        provenance_note = "\nIMPORTANT: Some of the data below is tagged 'synthetic' (simulated, not observed). If you reference any synthetic figures, you MUST clearly state they are simulated."

    prompt = f"""You are TransitSense, a transit decision-intelligence assistant. Below is the RAW NUMERIC OUTPUT from a deterministic skill call. Your job is to narrate these results in plain English and suggest a recommendation.

RULES:
- Do NOT change or recalculate any numbers. Only restate them.
- Every number you mention MUST appear verbatim in the raw output below.
- Be concise (2-4 sentences).
- Suggest one actionable recommendation.
{provenance_note}

Raw {skill_name} output:
{json.dumps(skill_output, indent=2)}

User's original query params: {json.dumps(route_params)}
"""

    import time
    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            break
        except genai_errors.APIError as e:
            last_error = e
            if "429" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return _narrate_template(route_params, skill_output, skill_name, has_synthetic)

    answer = response.text.strip()

    if not _check_fabrication(answer, skill_output):
        answer += "\n\n[Note: Some numbers in this response could not be verified against source data — review recommended.]"

    return answer


def _narrate_template(route_params, skill_output, skill_name, has_synthetic):
    """Template-based narration fallback when no Gemini key."""
    provenance = ""
    if has_synthetic:
        provenance = " (based on simulated data)"

    if skill_name == "delay_analysis":
        s = skill_output
        if s.get("insufficient_data"):
            return f"Not enough data for route {s['route_id']} to compute reliable statistics{provenance}."
        return (
            f"Route {s['route_id']} has an average delay of {s['avg_delay_min']} minutes "
            f"with an on-time percentage of {s['on_time_pct']}%{provenance}. "
            f"{len(s['anomaly_flags'])} severe delay anomalies were detected out of {s['row_count']} trips. "
            f"Recommendation: Investigate routes with on-time rates below 60% for schedule adjustments."
        )
    elif skill_name == "forecast":
        s = skill_output
        if s.get("low_confidence"):
            return f"Insufficient historical data to generate a reliable forecast for route {s['route_id']}{provenance}."
        vals = [f"{f['date']}: {f['value']} min" for f in s["forecast"]]
        return (
            f"Forecast for route {s['route_id']} ({s['metric']}) using {s['model_version']}: "
            f"{'; '.join(vals)}{provenance}. "
            f"Recommendation: Monitor the upward trend and consider schedule adjustments."
        )
    elif skill_name == "priority_scoring":
        s = skill_output
        if not s:
            return f"No routes could be scored{provenance}."
        top = s[0]
        return (
            f"Top priority route is {top['route_id']} with a composite score of {top['score']} "
            f"(avg delay: {top['contributing_factors']['avg_delay_min']}min, "
            f"on-time: {top['contributing_factors']['on_time_pct']}%, "
            f"ridership: {top['contributing_factors']['ridership']}){provenance}. "
            f"Recommendation: Focus schedule review and resource allocation on the top 3 ranked routes."
        )
    return "I couldn't process that query. Please try rephrasing."


def _expand_last_response(session):
    """Render a more detailed view of the last skill output."""
    last = session.get("last_output")
    skill = session.get("last_skill")
    if not last or not skill:
        return None

    if skill == "locality_status":
        if not last.get("found"):
            return None
        lines = [f"**Full details: {last['zone']}** — {last['total_routes']} routes"]
        for r in last["route_statuses"]:
            lines.append(
                f"  • Route {r['route_id']}: avg delay {r['avg_delay_min']}min, "
                f"on-time {r['on_time_pct']}%, {r['anomaly_count']} anomalies"
            )
        if last["solutions"]:
            lines.append("\n**All recommended actions:**")
            for s in last["solutions"]:
                for issue in s["issues"]:
                    lines.append(f"  • Route {s['route_id']}: {issue}")
        return "\n".join(lines)

    if skill == "delay_analysis":
        if last.get("insufficient_data"):
            return None
        lines = [
            f"**Detailed metrics for Route {last['route_id']}**",
            f"  Average delay: {last['avg_delay_min']} min",
            f"  On-time percentage: {last['on_time_pct']}%",
            f"  Total trips analyzed: {last['row_count']}",
        ]
        if last.get("anomaly_flags"):
            lines.append(f"\n  **All {len(last['anomaly_flags'])} anomalies:**")
            for a in last["anomaly_flags"][:10]:
                lines.append(f"  • {a.get('trip_id', '?')}: {a.get('delay_minutes', '?')}min ({a.get('source', '?')})")
        return "\n".join(lines)

    if skill == "priority_scoring":
        if not last:
            return None
        lines = ["**Full priority ranking:**"]
        for i, r in enumerate(last, 1):
            lines.append(
                f"  {i}. Route {r['route_id']}: score {r['score']} "
                f"(delay {r['contributing_factors']['avg_delay_min']}min, "
                f"on-time {r['contributing_factors']['on_time_pct']}%)"
            )
        return "\n".join(lines)

    if skill == "forecast":
        if last.get("low_confidence"):
            return None
        lines = [f"**Full forecast for Route {last['route_id']} ({last['metric']})**"]
        for f in last["forecast"]:
            lines.append(f"  • {f['date']}: {f['value']} {last['metric']}")
        return "\n".join(lines)

    return None


@app.post("/query", response_model=QueryResponse)
def handle_query(req: QueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Empty query")

    session = _get_session(req.session_id)
    route_params = parse_query(query)
    skill_name = route_params["target_skill"]

    # Check if we're awaiting a locality choice from a previous turn
    if session["awaiting_locality"]:
        zone_input = query.strip().lower()
        zones = find_zones(zone_input)
        if zones:
            session["awaiting_locality"] = False
            exact = next((z for z in zones if z["name"].lower() == zone_input), None)
            chosen = exact if exact else zones[0]
            resp = _handle_locality_status(chosen["name"], route_params)
            session.update(last_skill="locality_status", last_output=resp.skill_calls[-1] if resp.skill_calls else None, last_params=route_params)
            return resp
        session["awaiting_locality"] = False

    # Handle greeting
    if skill_name == "greeting":
        return QueryResponse(
            answer_text=(
                "Hey there! I'm TransitSense, your Hyderabad bus transit copilot.\n\n"
                "You can ask me things like:\n"
                "  • **How is Secunderabad doing?** — check route status in an area\n"
                "  • **What's the delay on route 219?** — delay analysis\n"
                "  • **Which routes are the worst right now?** — priority ranking\n"
                "  • **Recommendations for route 49M** — improvement suggestions\n\n"
                "What would you like to check?"
            ),
            cited_metrics={},
            source_skill="greeting",
            skill_calls=[route_params],
            data_provenance=None,
        )

    # Handle clarify
    if skill_name == "clarify":
        return QueryResponse(
            answer_text="I'm not sure what you're asking. Try asking about a route's delay, route priorities, a specific locality, or recommendations.",
            cited_metrics={},
            source_skill="clarify",
            skill_calls=[route_params],
            data_provenance=None,
        )

    # Handle locality_status
    if skill_name == "locality_status":
        locality = route_params.get("locality")
        if locality:
            resp = _handle_locality_status(locality, route_params)
            session.update(last_skill="locality_status", last_output=resp.skill_calls[-1] if resp.skill_calls else None, last_params=route_params)
            return resp
        # No locality specified — ask user to choose
        popular = find_zones()
        top_zones = [z["name"] for z in popular[:8]]
        session["awaiting_locality"] = True
        return QueryResponse(
            answer_text=(
                f"Which locality would you like to check?\n\n"
                + "\n".join(f"  • {z}" for z in top_zones)
                + "\n\nType a locality name or one of the above."
            ),
            cited_metrics={"available_zones": len(top_zones)},
            source_skill="locality_status",
            skill_calls=[route_params],
            data_provenance=None,
        )

    # Handle solutions
    if skill_name == "solutions":
        rid = route_params.get("route_id")
        if rid:
            stats = get_delay_stats(rid)
            session.update(last_skill="solutions", last_output=stats, last_params=route_params)
            return QueryResponse(
                answer_text=_generate_solutions_text(rid, stats),
                cited_metrics={"route_id": rid, "avg_delay_min": stats.get("avg_delay_min", 0)},
                source_skill="solutions",
                skill_calls=[route_params, stats],
                data_provenance="based on simulated data" if _check_synthetic_provenance(stats) else None,
            )
        return QueryResponse(
            answer_text="Which route would you like recommendations for? Mention a route number like route 219.",
            cited_metrics={},
            source_skill="solutions",
            skill_calls=[route_params],
            data_provenance=None,
        )

    # Handle delay_analysis with no route_id — expand or ask
    if skill_name == "delay_analysis":
        rid = route_params.get("route_id")
        if not rid:
            expanded = _expand_last_response(session)
            if expanded:
                return QueryResponse(
                    answer_text=expanded,
                    cited_metrics={},
                    source_skill="delay_analysis",
                    skill_calls=[route_params],
                    data_provenance=session.get("last_output", {}).get("data_provenance"),
                )
            return QueryResponse(
                answer_text="Which route would you like me to look into? Mention a route number like 277D or 219.",
                cited_metrics={},
                source_skill="delay_analysis",
                skill_calls=[route_params],
                data_provenance=None,
            )

    # Deterministic skills
    skill_output = None
    try:
        if skill_name == "delay_analysis":
            skill_output = get_delay_stats(
                route_params["route_id"],
                route_params.get("date_range"),
            )
        elif skill_name == "forecast":
            skill_output = forecast_metric(
                route_params["route_id"],
                route_params.get("metric", "delay"),
                7,
            )
        elif skill_name == "priority_scoring":
            skill_output = score_routes(
                route_params.get("date_range"),
            )
    except Exception as e:
        logger.error(f"Skill error: {e}")
        raise HTTPException(status_code=500, detail=f"Skill execution failed: {str(e)}")

    session.update(last_skill=skill_name, last_output=skill_output, last_params=route_params)

    has_synthetic = _check_synthetic_provenance(skill_output) if isinstance(skill_output, dict) else False
    data_provenance = "based on simulated data" if has_synthetic else None

    answer_text = _narrate_result(route_params, skill_output, skill_name)

    cited_metrics = {}
    if isinstance(skill_output, dict):
        for k, v in skill_output.items():
            if isinstance(v, (int, float, str)):
                cited_metrics[k] = v
            elif isinstance(v, list) and k == "anomaly_flags":
                cited_metrics["anomaly_count"] = len(v)

    return QueryResponse(
        answer_text=answer_text,
        cited_metrics=cited_metrics,
        source_skill=skill_name,
        skill_calls=[route_params, {"skill": skill_name, "output_summary": cited_metrics}],
        data_provenance=data_provenance,
    )


def _handle_locality_status(locality, route_params):
    """Handle locality status query and return response."""
    result = get_locality_status(locality, route_params.get("date_range"))
    if not result["found"]:
        popular = find_zones()
        top = [z["name"] for z in popular[:8]]
        return QueryResponse(
            answer_text=f"Locality '{locality}' not found. Try one of: {', '.join(top)}",
            cited_metrics={},
            source_skill="locality_status",
            skill_calls=[route_params],
            data_provenance=None,
        )

    lines = [f"📍 **{result['zone']}** — {result['total_routes']} routes operating"]
    for r in result["route_statuses"][:5]:
        lines.append(
            f"  • Route {r['route_id']}: avg delay {r['avg_delay_min']}min, "
            f"on-time {r['on_time_pct']}%, {r['anomaly_count']} anomalies"
        )
    if len(result["route_statuses"]) > 5:
        lines.append(f"  ... and {len(result['route_statuses']) - 5} more routes")

    # Solutions
    if result["solutions"]:
        lines.append("\n**Suggested actions:**")
        for s in result["solutions"][:3]:
            lines.append(f"  • Route {s['route_id']}: {s['issues'][0]}")
        if len(result["solutions"]) > 3:
            lines.append(f"  ... and {len(result['solutions']) - 3} more routes with recommendations")

    provenance = "based on simulated data" if any(
        r["row_count"] > 0 for r in result["route_statuses"]
    ) else None

    return QueryResponse(
        answer_text="\n".join(lines),
        cited_metrics={"zone": result["zone"], "total_routes": result["total_routes"]},
        source_skill="locality_status",
        skill_calls=[route_params, result],
        data_provenance=provenance,
    )


def _generate_solutions_text(route_id, stats):
    """Generate solution suggestions for a single route."""
    if stats.get("insufficient_data"):
        return f"Not enough data for route {route_id} to provide recommendations."

    lines = [f"**Recommendations for Route {route_id}**"]
    lines.append(f"  Current: avg delay {stats['avg_delay_min']}min, on-time {stats['on_time_pct']}%")
    lines.append("")

    issues = []
    if stats["on_time_pct"] < 60:
        issues.append("Increase schedule buffer by 2-3 minutes during peak hours to improve on-time rate")
    if stats["avg_delay_min"] > 10:
        issues.append("Investigate traffic congestion patterns — consider route realignment or express bypass")
    if stats["avg_delay_min"] <= 5 and stats["on_time_pct"] > 80:
        issues.append("Route performance is good. Maintain current schedule and monitor regularly")
        issues.append("Consider replicating this route's operational practices on underperforming routes")

    if not issues:
        issues.append("Monitor the route regularly — current metrics are within acceptable ranges")

    for i, issue in enumerate(issues, 1):
        lines.append(f"  {i}. {issue}")

    return "\n".join(lines)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
