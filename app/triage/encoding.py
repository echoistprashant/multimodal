"""Font-Encoding and Character Anomaly Detection.

Identifies garbled PDF text layers caused by missing ToUnicode CMap tables,
custom font encodings, substitution glyphs (e.g., U+FFFD), or unprintable control sequences.
"""

import unicodedata


def calculate_printable_ratio(text: str) -> float:
    """Calculate ratio of printable characters against total length."""
    if not text:
        return 0.0

    printable_count = sum(1 for char in text if (char.isprintable() or char in "\r\n\t") and char != "\ufffd")
    return round(printable_count / len(text), 4)


def detect_encoding_anomalies(text: str) -> tuple[bool, float]:
    """Detect if text layer is corrupted by bad font glyph mapping.

    Returns:
        (is_anomalous, anomaly_ratio)
    """
    if not text:
        return False, 0.0

    total_len = len(text)
    replacement_chars = text.count("\ufffd") + text.count("\x00")
    control_chars = sum(1 for c in text if unicodedata.category(c).startswith("C") and c not in "\r\n\t")

    anomaly_count = replacement_chars + control_chars
    anomaly_ratio = round(anomaly_count / total_len, 4)

    # If more than 5% of characters are broken replacement glyphs or controls, text layer is corrupted
    is_anomalous = anomaly_ratio > 0.05
    return is_anomalous, anomaly_ratio
