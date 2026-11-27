"""Lightweight Zero-Cost Reranker for Hybrid RAG Results."""

import re
from typing import List
from app.rag.embed_schema import VectorSearchResult


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def rerank_results(
    query: str,
    candidates: List[VectorSearchResult],
    top_k: int = 5,
) -> List[VectorSearchResult]:
    """Re-score RRF candidates by combining fusion score with query term coverage."""
    q_terms = _token_set(query)
    if not q_terms or not candidates:
        return candidates[:top_k]

    reranked: List[VectorSearchResult] = []
    for cand in candidates:
        c_terms = _token_set(cand.chunk.text)
        overlap = len(q_terms & c_terms) / len(q_terms)
        # Boost RRF score with exact query-term coverage
        final_score = round(0.4 * cand.score + 0.6 * overlap, 6)
        reranked.append(
            VectorSearchResult(
                chunk=cand.chunk,
                score=final_score,
                source="hybrid_reranked",
            )
        )

    reranked.sort(key=lambda r: -r.score)
    return reranked[:top_k]
