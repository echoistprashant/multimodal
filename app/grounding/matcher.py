"""Text Normalizer and Fuzzy String Matcher for OCR/PDF Grounding.

Provides Levenshtein edit-distance similarity scoring and text canonicalization
to match extracted LLM values back to noisy OCR tokens.
"""

import re
import unicodedata


def normalize_for_matching(text: str) -> str:
    """Canonicalize text by normalizing Unicode, lowercasing, and collapsing whitespace."""
    if not text:
        return ""
    # NFKC normalization handles ligatures and full-width characters
    normalized = unicodedata.normalize("NFKC", text).lower()
    # Replace punctuation separators with spaces, keep alphanumeric and basic symbols
    normalized = re.sub(r"[^\w\s./-]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute iterative Levenshtein edit distance between two strings."""
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    if len(s1) < len(s2):
        s1, s2 = s2, s1

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def compute_fuzzy_similarity(query: str, candidate: str) -> float:
    """Compute normalized similarity score in [0.0, 1.0] between query and candidate."""
    norm_q = normalize_for_matching(query)
    norm_c = normalize_for_matching(candidate)

    if not norm_q or not norm_c:
        return 0.0
    if norm_q == norm_c:
        return 1.0

    max_len = max(len(norm_q), len(norm_c))
    dist = levenshtein_distance(norm_q, norm_c)
    return round(max(0.0, 1.0 - (dist / max_len)), 4)
