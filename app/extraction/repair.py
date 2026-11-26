"""Resilient JSON Repair and Formatting Sanitizer.

Recovers parseable JSON from imperfect LLM responses containing markdown code fences,
trailing commas, unescaped quotes, or conversational preamble text.
"""

import json
import re
from typing import Any, Dict


def extract_json_candidate_substring(raw_text: str) -> str:
    """Isolate the outermost JSON object substring enclosed between { and }."""
    # First check for standard markdown code blocks
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text, re.I)
    candidate = fence_match.group(1).strip() if fence_match else raw_text.strip()

    first_brace = candidate.find("{")
    last_brace = candidate.rfind("}")

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return candidate[first_brace : last_brace + 1]

    return candidate


def repair_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """Parse JSON string with resilient fallback repair heuristics for LLM outputs.

    Args:
        raw_text: Raw output string from language model.

    Returns:
        Parsed Python dictionary.

    Raises:
        ValueError: If JSON cannot be recovered even after heuristic repairs.
    """
    candidate = extract_json_candidate_substring(raw_text)

    # 1. Attempt standard parse
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}
    except json.JSONDecodeError:
        pass

    # 2. Heuristic repair: remove trailing commas before closing braces/brackets
    repaired = re.sub(r",\s*([\]}])", r"\1", candidate)

    # 3. Replace single quotes around keys/values with double quotes
    # (Matches 'key': -> "key":)
    repaired = re.sub(r"(?<=[{\s,])\'([A-Za-z0-9_]+)\'\s*:", r'"\1":', repaired)

    try:
        parsed = json.loads(repaired)
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}
    except json.JSONDecodeError as err:
        raise ValueError(f"Failed to repair and parse JSON from model output: {err}\nCandidate: {candidate[:200]}")
