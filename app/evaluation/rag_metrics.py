"""RAG Retrieval Evaluation Metrics (Recall@K and Mean Reciprocal Rank)."""

from typing import List, Set


def compute_recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 5) -> float:
    """Compute Recall@K: fraction of relevant items appearing in top-K retrieved results."""
    if not relevant_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    hits = len(top_k & relevant_ids)
    return round(hits / len(relevant_ids), 4)


def compute_mrr(ranked_lists: List[List[str]], relevant_sets: List[Set[str]]) -> float:
    """Compute Mean Reciprocal Rank (MRR) across a batch of RAG queries."""
    if not ranked_lists or len(ranked_lists) != len(relevant_sets):
        return 0.0

    reciprocal_ranks: List[float] = []
    for retrieved, relevant in zip(ranked_lists, relevant_sets):
        rr = 0.0
        for rank, item_id in enumerate(retrieved, start=1):
            if item_id in relevant:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    return round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4)
