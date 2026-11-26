"""Extraction Payload Post-Processing and Anti-Hallucination Normalization.

Cleans null placeholder artifacts (e.g. 'N/A', 'None', '-'), strips whitespace,
and coerces currency formats into valid schema inputs.
"""

import re
from typing import Any, Dict

NULL_EQUIVALENT_STRINGS = {
    "n/a", "na", "none", "nil", "null", "not available",
    "not applicable", "not provided", "unknown", "-", "--", "---", "",
}


def clean_extracted_value(val: Any) -> Any:
    """Normalize extracted value, converting placeholder strings to None."""
    if isinstance(val, str):
        cleaned_str = val.strip()
        if cleaned_str.lower() in NULL_EQUIVALENT_STRINGS:
            return None
        return cleaned_str

    if isinstance(val, dict):
        return {k: clean_extracted_value(v) for k, v in val.items()}

    if isinstance(val, list):
        return [clean_extracted_value(item) for item in val]

    return val


def coerce_monetary_value(val: Any) -> float | None:
    """Extract clean float from monetary representation (e.g. '$1,250.50' -> 1250.50)."""
    if val is None:
        return None

    if isinstance(val, (int, float)):
        return float(val)

    if isinstance(val, str):
        cleaned = val.strip().replace("$", "").replace("€", "").replace("£", "").replace("₹", "")
        cleaned = cleaned.replace(",", "").strip()
        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None

    return None


def sanitize_extraction_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply holistic sanitization and null normalization to LLM extraction dictionary."""
    sanitized: Dict[str, Any] = {}

    for k, v in data.items():
        cleaned_val = clean_extracted_value(v)

        # Monetary field coercion
        if any(term in k.lower() for term in ["amount", "subtotal", "tax", "total", "price"]):
            if isinstance(cleaned_val, str):
                cleaned_val = coerce_monetary_value(cleaned_val)

        sanitized[k] = cleaned_val

    return sanitized
