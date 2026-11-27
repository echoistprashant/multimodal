"""Unit tests for Phase 10 Part 10.1: Fuzzy Matching and Multi-Token Span Alignment."""

from app.grounding.aligner import find_matching_token_spans
from app.grounding.bbox_merger import is_valid_normalized_bbox, merge_bounding_boxes
from app.grounding.matcher import compute_fuzzy_similarity, levenshtein_distance, normalize_for_matching


def test_fuzzy_matcher_and_normalizer() -> None:
    """Verify Unicode normalization, Levenshtein distance, and fuzzy similarity."""
    assert normalize_for_matching("Acme  Logistics, Corp.") == "acme logistics corp."
    assert levenshtein_distance("invoice", "invo1ce") == 1
    sim = compute_fuzzy_similarity("Acme Logistics Corp", "Acme L0gistics Corp.")
    assert sim >= 0.88


def test_bbox_merger_and_validation() -> None:
    """Verify bounding box unioning and normalized coordinate clamping."""
    merged = merge_bounding_boxes([
        (0.10, 0.20, 0.30, 0.25),
        (0.32, 0.20, 0.55, 0.26),
    ])
    assert merged == (0.10, 0.20, 0.55, 0.26)
    assert is_valid_normalized_bbox(merged) is True
    assert is_valid_normalized_bbox((0.6, 0.2, 0.4, 0.5)) is False


def test_sliding_window_span_alignment() -> None:
    """Verify multi-token extracted value aligns to merged token bounding box."""
    tokens = [
        {"id": "t1", "text": "Vendor:", "bbox": (0.05, 0.10, 0.15, 0.13)},
        {"id": "t2", "text": "Global", "bbox": (0.17, 0.10, 0.25, 0.13)},
        {"id": "t3", "text": "Tech", "bbox": (0.26, 0.10, 0.32, 0.13)},
        {"id": "t4", "text": "Solutions", "bbox": (0.33, 0.10, 0.44, 0.13)},
        {"id": "t5", "text": "Invoice", "bbox": (0.05, 0.20, 0.15, 0.23)},
    ]

    spans = find_matching_token_spans("Global Tech Solutions", tokens, page_no=1)
    assert len(spans) >= 1
    best = spans[0]
    assert best.match_score == 1.0
    assert best.bbox == (0.17, 0.10, 0.44, 0.13)
    assert best.token_ids == ["t2", "t3", "t4"]
