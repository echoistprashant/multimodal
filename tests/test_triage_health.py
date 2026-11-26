"""Unit tests for Phase 6 Part 6.1: Text Layer Health and Garble Detection."""

from app.triage.density import analyze_text_layer_health, calculate_word_quality_ratio
from app.triage.encoding import calculate_printable_ratio, detect_encoding_anomalies


def test_clean_text_layer_health() -> None:
    """Verify clean digital invoice text yields high health score and zero garble."""
    clean_text = (
        "INVOICE #1042\n"
        "Date: 2026-11-25\n"
        "Vendor: Acme Logistics Corp\n"
        "Subtotal: $1,000.00\n"
        "Tax (18%): $180.00\n"
        "Total Amount Due: $1,180.00\n"
    )
    health = analyze_text_layer_health(clean_text, token_count=18)
    assert health.has_text_layer is True
    assert health.is_garbled is False
    assert health.printable_ratio > 0.95
    assert health.alpha_ratio > 0.80
    assert health.health_score > 0.85


def test_garbled_encoding_detection() -> None:
    """Verify corrupted text layer containing replacement glyphs is flagged as garbled."""
    corrupted_text = (
        "\ufffd\ufffd\ufffd\x01\x02\x03\ufffd\ufffd"
        "Inv\ufffdoice T\ufffdtal"
        "\x00\x04\x05\x06\ufffd\ufffd"
    )
    is_anomalous, ratio = detect_encoding_anomalies(corrupted_text)
    assert is_anomalous is True
    assert ratio > 0.20

    health = analyze_text_layer_health(corrupted_text, token_count=5)
    assert health.is_garbled is True
    assert health.health_score == 0.0


def test_empty_and_sparse_text() -> None:
    """Verify pages with virtually no text layer return has_text_layer=False."""
    health_empty = analyze_text_layer_health("", token_count=0)
    assert health_empty.has_text_layer is False
    assert health_empty.health_score == 0.0

    health_sparse = analyze_text_layer_health("Hi", token_count=1)
    assert health_sparse.has_text_layer is False


def test_word_quality_ratio() -> None:
    """Verify calculation of valid words vs gibberish strings."""
    valid_text = "Acme Corp Monthly Subscription Payment"
    ratio = calculate_word_quality_ratio(valid_text)
    assert ratio == 1.0

    nonsense_text = "###@@@ !!! ??? $$$$ %%%%%"
    assert calculate_word_quality_ratio(nonsense_text) == 0.0
