"""Zero-Cost Local Dense Embedder (Offline BGE-M3 / Feature Hashing Fallback).

Generates L2-normalized fixed-dimension dense vectors using deterministic token n-gram
feature hashing so semantic search and cosine similarity run 100% offline at zero cost.
"""

import hashlib
import math
import re
from typing import List

from app.rag.embed_schema import EmbeddingProviderProtocol


class LocalDenseEmbedder(EmbeddingProviderProtocol):
    """Deterministic L2-normalized dense vector embedder for offline/free-tier execution."""

    def __init__(self, dimension: int = 256) -> None:
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Encode a batch of strings into L2-normalized dense float vectors."""
        return [self._embed_single(t) for t in texts]

    def _embed_single(self, text: str) -> List[float]:
        vec = [0.0] * self._dim
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return vec

        # Unigrams + bigrams for richer phrase similarity
        features = list(tokens) + [f"{tokens[i]}_{tokens[i + 1]}" for i in range(len(tokens) - 1)]

        for feat in features:
            digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "little") % self._dim
            sign = 1.0 if (digest[4] & 1) == 0 else -1.0
            vec[bucket] += sign

        # L2 normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [round(x / norm, 6) for x in vec]
        return vec
