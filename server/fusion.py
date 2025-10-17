"""Score fusion and reranking utilities."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List, Optional

import numpy as np

from .models import RetrievedChunk

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None  # type: ignore


@dataclass(slots=True)
class RerankConfig:
    model_name: str = "BAAI/bge-reranker-v2-m3"
    top_k: int = 10
    boost_fact: float = 1.1


class Reranker:
    """Optional cross-encoder reranking."""

    def __init__(self, config: Optional[RerankConfig] = None) -> None:
        self.config = config or RerankConfig()
        self.model = None
        if CrossEncoder is not None:
            try:
                self.model = CrossEncoder(self.config.model_name)
            except Exception as exc:
                logger.warning("Failed to load cross-encoder (%s). Falling back to baseline: %s", self.config.model_name, exc)

    def rerank(self, query: str, candidates: Iterable[RetrievedChunk], top_k: Optional[int] = None) -> List[RetrievedChunk]:
        top_k = top_k or self.config.top_k
        items = list(candidates)

        if not items:
            return []

        if self.model is None:
            logger.debug("Cross-encoder unavailable; returning baseline scores.")
            items.sort(key=lambda chunk: chunk.score, reverse=True)
            return items[:top_k]

        pairs = [(query, chunk.text) for chunk in items]
        scores = self.model.predict(pairs)
        reranked: List[RetrievedChunk] = []
        for score, chunk in zip(scores, items, strict=True):
            adjusted = float(score)
            if chunk.source_type == "fact":
                adjusted *= self.config.boost_fact
            reranked.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    source_type=chunk.source_type,
                    score=adjusted,
                    metadata=chunk.metadata,
                )
            )
        reranked.sort(key=lambda chunk: chunk.score, reverse=True)
        return reranked[:top_k]
