#!/usr/bin/env python3
"""
TransitSense NL Query Router Skill.
Uses Gemini to parse free-text questions into structured skill-call params.
Returns only structured parameters — never numeric values, never narrative.
"""
import json
import os
import re
import time

def parse_query(text):
    """
    Parse a natural-language query into structured skill parameters.

    Uses Gemini API if available; falls back to simple keyword matching
    when the API key is not set (for offline testing).

    Returns:
        dict with target_skill, route_id, metric, date_range, confidence.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if api_key and api_key != "your_key_here":
        return _parse_with_gemini(text, api_key)
    else:
        return _parse_with_keywords(text)


def _parse_with_keywords(text):
    """Simple keyword-based parser for offline testing."""
    text_lower = text.lower()

    # Greeting detection (highest priority — checked before anything else)
    if any(text_lower.strip().startswith(w) for w in ["hello", "hi", "hey", "howdy", "greetings", "yo"]) or \
       any(w in text_lower for w in ["good morning", "good afternoon", "good evening", "good day", "what's up"]):
        return {
            "target_skill": "greeting",
            "route_id": None,
            "metric": None,
            "date_range": None,
            "locality": None,
            "confidence": 0.95,
        }

    # Detect locality/status intent (check first so it doesn't get caught by other intents)
    is_locality = any(w in text_lower for w in [
        "current status", "how is", "status of", "locality", "area",
        "what's happening in", "what is happening in", "routes in",
        "status", "how's", "how are things", "what's going on", "how's it going",
    ])
    locality_keywords = ["current status", "how is", "status of", "locality", "area",
                         "what's happening in", "what is happening in", "routes in",
                         "status", "how's", "how are things", "what's going on", "how's it going"]

    # Check if a known locality name is directly mentioned
    from skills.locality_status import find_zones
    locality_name = None
    popular = find_zones()
    popular_names_lower = {z["name"].lower(): z["name"] for z in popular}
    for zone_lower, zone_original in popular_names_lower.items():
        if zone_lower in text_lower:
            locality_name = zone_original
            is_locality = True
            break

    if is_locality:
        return {
            "target_skill": "locality_status",
            "route_id": None,
            "metric": None,
            "date_range": None,
            "locality": locality_name,
            "confidence": 0.7 if locality_name else 0.5,
        }

    # Detect solution/advice intent
    if any(w in text_lower for w in ["solution", "advice", "recommend", "fix", "improve", "what should"]):
        target_skill = "solutions"
    elif any(w in text_lower for w in ["priority", "rank", "worst", "best", "most important", "score"]):
        target_skill = "priority_scoring"
    elif any(w in text_lower for w in ["forecast", "predict", "future", "will be", "trend", "expect"]):
        target_skill = "forecast"
    elif any(w in text_lower for w in ["delay", "late", "on-time", "ontime", "on time", "performance", "punctual",
                                       "detailed", "details", "tell me", "more about", "explain", "what about", "how about"]):
        target_skill = "delay_analysis"
    else:
        return {
            "target_skill": "clarify",
            "route_id": None,
            "metric": None,
            "date_range": None,
            "locality": None,
            "confidence": 0.3,
        }

    # Extract route_id
    route_match = re.search(r'\broute\s*(\d+[A-Za-z]*(?:/\d+[A-Za-z]*)*)\b', text, re.IGNORECASE)
    route_id = route_match.group(1) if route_match else None

    # Extract date range
    date_range = None
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})\s*(?:to|through|-|–)\s*(\d{4}-\d{2}-\d{2})', text)
    if date_match:
        date_range = [date_match.group(1), date_match.group(2)]
    else:
        single_date = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if single_date:
            date_range = [single_date.group(1), single_date.group(1)]

    # Extract metric for forecast
    metric = None
    if target_skill == "forecast":
        if "ridership" in text_lower or "rider" in text_lower or "passenger" in text_lower:
            metric = "ridership"
        else:
            metric = "delay"

    confidence = 0.6 if route_id else 0.5

    return {
        "target_skill": target_skill,
        "route_id": route_id,
        "metric": metric,
        "date_range": date_range,
        "locality": None,
        "confidence": round(confidence, 2),
    }


def _parse_with_gemini(text, api_key):
    """Use Gemini to parse query into structured params."""
    from google import genai
    from google.genai import errors as genai_errors

    client = genai.Client(api_key=api_key)

    prompt = f"""You are a transit query router. Parse the user's question into structured parameters.

Return ONLY a JSON object with these fields:
- target_skill: one of "greeting", "delay_analysis", "forecast", "priority_scoring", "locality_status", "solutions", or "clarify"
- route_id: string or null (e.g. "219", "49M")
- metric: "delay" or "ridership" or null
- date_range: [start_date, end_date] in YYYY-MM-DD format, or null
- locality: string or null — zone/locality name if query asks about an area (e.g. "Secunderabad", "Charminar")
- confidence: float between 0 and 1

Rules:
- Use "greeting" if the query is a greeting or casual chat ("hello", "hi", "how are you", "good morning")
- Use "locality_status" if the user asks about current conditions in a locality/area ("how is Secunderabad", "current status", "routes in Charminar")
- Use "solutions" if the user asks for recommendations or fixes ("what should I do", "recommendations for route 219", "how to fix delays")
- If the query is ambiguous (no route, no clear intent), set target_skill to "clarify"
- Do NOT include any numeric values other than route/stop IDs
- Do NOT include any narrative text
- Return valid JSON only

User query: {text}
"""

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
            return _parse_with_keywords(text)

    raw = response.text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "target_skill": "clarify",
            "route_id": None,
            "metric": None,
            "date_range": None,
            "confidence": 0.0,
        }

    # Validate fields
    valid_skills = {"delay_analysis", "forecast", "priority_scoring", "locality_status", "solutions", "clarify", "greeting"}
    if result.get("target_skill") not in valid_skills:
        result["target_skill"] = "clarify"

    return {
        "target_skill": result.get("target_skill", "clarify"),
        "route_id": result.get("route_id"),
        "metric": result.get("metric"),
        "date_range": result.get("date_range"),
        "locality": result.get("locality"),
        "confidence": min(1.0, max(0.0, result.get("confidence", 0.0))),
    }
