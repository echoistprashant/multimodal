"""Text Density and Vocabulary Quality Evaluator.

Analyzes character densities, alphanumeric ratios, and plausible dictionary word
structures to determine whether native text extraction is clean enough to bypass OCR.
"""

import re
from app.triage.encoding import calculate_printable_ratio, detect_encoding_anomalies
from app.triage.schema import TextLayerHealth

# Simple regex pattern for natural human language words
WORD_PATTERN = re.compile(r"^[A-Za-z0-9$€£.,%/#-]+$")


def calculate_word_quality_ratio(text: str) -> float:
    """Calculate the fraction of whitespace-delimited tokens that form plausible words."""
    tokens = text.strip().split()
    if not tokens:
        return 0.0

    valid_words = 0
    for tok in tokens:
        # A plausible word has alphanumeric content and reasonable length
        if WORD_PATTERN.match(tok) and len(tok) <= 45:
            valid_words += 1

    return round(valid_words / len(tokens), 4)


def analyze_text_layer_health(raw_text: str, token_count: int = 0) -> TextLayerHealth:
    """Analyze embedded PDF text layer and produce comprehensive quality health assessment."""
    clean_text = raw_text.strip()
    total_chars = len(clean_text)

    if total_chars < 15 or token_count == 0:
        return TextLayerHealth(
            has_text_layer=False,
            total_characters=total_chars,
            printable_ratio=0.0,
            alpha_ratio=0.0,
            dictionary_word_ratio=0.0,
            is_garbled=False,
            health_score=0.0,
        )

    printable_ratio = calculate_printable_ratio(clean_text)
    is_anomalous, _ = detect_encoding_anomalies(clean_text)

    # Calculate alphanumeric ratio
    alpha_chars = sum(1 for c in clean_text if c.isalnum() or c.isspace())
    alpha_ratio = round(alpha_chars / total_chars, 4)

    word_ratio = calculate_word_quality_ratio(clean_text)

    # Flag as garbled if non-printable or severely low alphanumeric/word ratio
    is_garbled = is_anomalous or printable_ratio < 0.85 or word_ratio < 0.40

    # Composite health score [0.0, 1.0]
    if is_garbled:
        health_score = 0.0
    else:
        health_score = round(
            0.4 * printable_ratio + 0.3 * alpha_ratio + 0.3 * word_ratio,
            4,
        )

    return TextLayerHealth(
        has_text_layer=True,
        total_characters=total_chars,
        printable_ratio=printable_ratio,
        alpha_ratio=alpha_ratio,
        dictionary_word_ratio=word_ratio,
        is_garbled=is_garbled,
        health_score=health_score,
    )
