"""Reciprocal Rank Fusion (RRF) for Hybrid Dense + Lexical Search."""

from typing import Dict, List
from app.rag.embed_schema import VectorSearchResult


def reciprocal_rank_fusion(
    dense_results: List[VectorSearchResult],
    lexical_results: List[VectorSearchResult],
    k: int = 60,
    dense_weight: float = 0.5,
    lexical_weight: float = 0.5,
) -> List[VectorSearchResult]:
    """Fuse dense vector and BM25 rankings using weighted Reciprocal Rank Fusion.

    RRF_score(d) = sum(weight / (k + rank_i(d)))
    """
    scores: Dict[str, float] = {}
    chunk_map: Dict[str, VectorSearchResult] = {}

    for rank, res in enumerate(dense_results, start=1):
        cid = res.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + (dense_weight / (k + rank))
        chunk_map[cid] = res

    for rank, res in enumerate(lexical_results, start=1):
        cid = res.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + (lexical_weight / (k + rank))
        if cid not in chunk_map:
            chunk_map[cid] = res

    fused: List[VectorSearchResult] = [
        VectorSearchResult(
            chunk=chunk_map[cid].chunk,
            score=round(score, 6),
            source="hybrid",
        )
        for cid, score in scores.items()
    ]
    fused.sort(key=lambda r: -r.score)
    return fused
