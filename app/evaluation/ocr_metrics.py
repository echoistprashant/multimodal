"""OCR Quality and Error Rate Evaluation Metrics.

Implements Character Error Rate (CER) and Word Error Rate (WER) using
Levenshtein edit distance over reference ground truth transcriptions.
"""

from typing import Any


def compute_edit_distance(seq_a: list[Any] | str, seq_b: list[Any] | str) -> int:
    """Calculate minimum edit distance (insertions, deletions, substitutions) via dynamic programming."""
    len_a = len(seq_a)
    len_b = len(seq_b)

    # Initialize DP matrix: (len_a + 1) x (len_b + 1)
    dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]

    for i in range(len_a + 1):
        dp[i][0] = i
    for j in range(len_b + 1):
        dp[0][j] = j

    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            if seq_a[i - 1] == seq_b[j - 1]:
                cost = 0
            else:
                cost = 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,        # Deletion
                dp[i][j - 1] + 1,        # Insertion
                dp[i - 1][j - 1] + cost,  # Substitution
            )

    return dp[len_a][len_b]


def compute_cer(reference: str, hypothesis: str) -> float:
    """Calculate Character Error Rate (CER).

    Formula: (Substitutions + Insertions + Deletions) / Reference Character Count
    """
    ref_chars = list(reference)
    hyp_chars = list(hypothesis)

    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0

    distance = compute_edit_distance(ref_chars, hyp_chars)
    return round(distance / len(ref_chars), 4)


def compute_wer(reference: str, hypothesis: str) -> float:
    """Calculate Word Error Rate (WER).

    Formula: (Substitutions + Insertions + Deletions) / Reference Word Count
    """
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    distance = compute_edit_distance(ref_words, hyp_words)
    return round(distance / len(ref_words), 4)


def evaluate_transcription(reference: str, hypothesis: str) -> dict[str, float]:
    """Compute consolidated transcription benchmark report."""
    return {
        "cer": compute_cer(reference, hypothesis),
        "wer": compute_wer(reference, hypothesis),
        "accuracy": round(max(0.0, 1.0 - compute_cer(reference, hypothesis)), 4),
    }
