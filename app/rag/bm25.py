"""BM25 Lexical Scorer for Exact Keyword, SKU, and Invoice-ID Retrieval."""

import math
import re
from collections import Counter
from typing import Dict, List

from app.rag.chunk_schema import MultimodalChunk
from app.rag.embed_schema import VectorSearchResult


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9_-]+", text.lower())


class BM25Scorer:
    """Okapi BM25 lexical ranking engine for exact term and identifier matching."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

    def search(
        self,
        query: str,
        chunks: List[MultimodalChunk],
        top_k: int = 5,
    ) -> List[VectorSearchResult]:
        """Rank chunks against query using Okapi BM25."""
        if not chunks or not query.strip():
            return []

        query_terms = _tokenize(query)
        if not query_terms:
            return []

        doc_tokens = [_tokenize(c.text) for c in chunks]
        n_docs = len(chunks)
        avg_dl = sum(len(dt) for dt in doc_tokens) / max(n_docs, 1)

        # Document frequency per term
        df: Dict[str, int] = Counter()
        for dt in doc_tokens:
            for term in set(dt):
                df[term] += 1

        results: List[VectorSearchResult] = []
        for chunk, dt in zip(chunks, doc_tokens):
            dl = len(dt)
            if dl == 0:
                continue
            tf_counts = Counter(dt)
            score = 0.0
            for qt in query_terms:
                if qt not in tf_counts:
                    continue
                tf = tf_counts[qt]
                doc_freq = df.get(qt, 0)
                idf = math.log(1.0 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
                denom = tf + self.k1 * (1.0 - self.b + self.b * (dl / max(avg_dl, 1e-6)))
                score += idf * ((tf * (self.k1 + 1.0)) / max(denom, 1e-6))

            if score > 0.0:
                results.append(VectorSearchResult(chunk=chunk, score=round(score, 6), source="bm25"))

        results.sort(key=lambda r: -r.score)
        return results[:top_k]
