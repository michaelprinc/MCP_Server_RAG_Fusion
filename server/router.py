"""Query routing and intent classification."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RouterConfig:
    mode: str = "classifier"
    classifier_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    threshold: float = 0.7
    labeled_examples_path: Optional[Path] = None


class QueryRouter:
    """Route queries to factual, experiential, or hybrid retrieval."""

    def __init__(self, config: Optional[RouterConfig] = None) -> None:
        self.config = config or RouterConfig()
        self.model = SentenceTransformer(self.config.classifier_model)
        self.label_embeddings = self._load_label_embeddings()

    def _load_label_embeddings(self) -> Dict[str, List[float]]:
        labels = {
            "factual": "technical specification, manual, settings, maximum",
            "experiential": "best practice, troubleshooting, in practice, field report",
            "hybrid": "procedure, step by step, recommended approach",
        }
        embeddings = {
            label: self.model.encode(text, convert_to_numpy=True)
            for label, text in labels.items()
        }
        return embeddings

    def classify(self, query: str) -> str:
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        scores = {}
        for label, embedding in self.label_embeddings.items():
            similarity = float(query_embedding @ embedding / (self._norm(query_embedding) * self._norm(embedding)))
            scores[label] = similarity
        best_label = max(scores, key=scores.get)
        logger.debug("Router scores: %s -> %s", scores, best_label)
        return best_label

    @staticmethod
    def _norm(vector) -> float:
        return float((vector**2).sum() ** 0.5)
