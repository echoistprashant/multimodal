"""Sliding-Window Multi-Token Span Aligner.

Finds contiguous sequences of page tokens that match multi-word extracted values
(e.g., vendor names, addresses, descriptions) using exact or fuzzy matching.
"""

from typing import List, Sequence, Tuple
from app.grounding.matcher import compute_fuzzy_similarity, normalize_for_matching
from app.grounding.schema import GroundedSpan
from app.grounding.bbox_merger import merge_bounding_boxes


def find_matching_token_spans(
    target_value: str,
    page_tokens: Sequence[dict],
    page_no: int = 1,
    min_similarity: float = 0.80,
    max_window_padding: int = 2,
) -> List[GroundedSpan]:
    """Search ordered page tokens with a sliding window for spans matching target_value.

    Args:
        target_value: Extracted string value to locate on the page.
        page_tokens: Sequence of token dicts containing 'text', 'bbox', and optional 'id'.
        page_no: 1-based page number.
        min_similarity: Minimum Levenshtein similarity threshold in [0.0, 1.0].
        max_window_padding: Extra tokens allowed around expected word count.

    Returns:
        List of GroundedSpan sorted descending by match_score.
    """
    norm_target = normalize_for_matching(target_value)
    if not norm_target or not page_tokens:
        return []

    target_word_count = max(1, len(norm_target.split()))
    min_win = max(1, target_word_count - 1)
    max_win = min(len(page_tokens), target_word_count + max_window_padding)

    candidates: List[GroundedSpan] = []

    for start_idx in range(len(page_tokens)):
        for win_len in range(min_win, max_win + 1):
            end_idx = start_idx + win_len
            if end_idx > len(page_tokens):
                break

            window = page_tokens[start_idx:end_idx]
            window_text = " ".join(str(t.get("text", "")).strip() for t in window).strip()
            if not window_text:
                continue

            score = compute_fuzzy_similarity(norm_target, window_text)
            if score >= min_similarity:
                boxes: List[Tuple[float, float, float, float]] = [
                    tuple(t["bbox"]) for t in window if "bbox" in t  # type: ignore[misc]
                ]
                merged_bbox = merge_bounding_boxes(boxes)
                token_ids = [str(t.get("id", f"tok_{start_idx + i}")) for i, t in enumerate(window)]

                candidates.append(
                    GroundedSpan(
                        page_no=page_no,
                        bbox=merged_bbox,
                        source_text=window_text,
                        token_ids=token_ids,
                        match_score=score,
                    )
                )

    # Sort best score first, then prefer tighter spans (fewer tokens)
    candidates.sort(key=lambda s: (-s.match_score, len(s.token_ids)))
    return candidates
