"""Hybrid retrieval across factual and experiential indexes."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

from .models import RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrievalWeights:
    fact_weight: float = 0.6
    example_weight: float = 0.4
    bm25_weight: float = 0.3
    dense_weight: float = 0.7


@dataclass(slots=True)
class RetrievalConfig:
    index_dir: Path = Path("data/indexes")
    weights: RetrievalWeights = field(default_factory=RetrievalWeights)
    top_k_initial: int = 50
    top_k_rerank: int = 10

    @classmethod
    def default(cls) -> "RetrievalConfig":
        return cls()


class IndexStore:
    def __init__(self, index_dir: Path) -> None:
        self.index_dir = index_dir
        self.fact_chunks: List[RetrievedChunk] = []
        self.example_chunks: List[RetrievedChunk] = []
        self.chunk_lookup: Dict[str, RetrievedChunk] = {}
        self.index_version = "unknown"
        self._load()

    def _load(self) -> None:
        manifest_path = self.index_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("Manifest not found at %s", manifest_path)
            return

        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
            self.index_version = manifest.get("version", "unknown")

        fact_path = self.index_dir / "chunks_fact.jsonl"
        example_path = self.index_dir / "chunks_example.jsonl"
        self.fact_chunks = list(self._load_chunks(fact_path, "fact"))
        self.example_chunks = list(self._load_chunks(example_path, "example"))

    def _load_chunks(self, path: Path, source_type: str) -> Iterable[RetrievedChunk]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = json.loads(line)
                chunk = RetrievedChunk(
                    chunk_id=payload["chunk_id"],
                    text=payload.get("text", ""),
                    source_type=source_type,
                    score=0.0,
                    metadata=payload.get("metadata", {}),
                )
                self.chunk_lookup[chunk.chunk_id] = chunk
                yield chunk


class Retriever:
    """Executes hybrid retrieval with basic score fusion."""

    def __init__(self, config: RetrievalConfig) -> None:
        self.config = config
        self.store = IndexStore(config.index_dir)

    @classmethod
    def from_config(cls, config_path: Optional[Path] = None) -> "Retriever":
        return cls(RetrievalConfig.default())

    @property
    def index_version(self) -> str:
        return self.store.index_version

    def reload(self) -> None:
        self.store = IndexStore(self.config.index_dir)

    def chunks_by_id(self, chunk_ids: Iterable[str]) -> List[RetrievedChunk]:
        return [
            self.store.chunk_lookup[chunk_id]
            for chunk_id in chunk_ids
            if chunk_id in self.store.chunk_lookup
        ]

    def retrieve(self, query: str, intent: str, top_k: int = 10) -> List[RetrievedChunk]:
        if intent not in {"factual", "experiential", "hybrid", "fact", "example"}:
            raise ValueError(f"Unsupported intent: {intent}")

        fact_results = self._score_chunks(query, self.store.fact_chunks)
        example_results = self._score_chunks(query, self.store.example_chunks)

        combined = self._fuse_results(intent, fact_results, example_results)
        combined.sort(key=lambda chunk: chunk.score, reverse=True)
        return combined[:top_k]

    def _score_chunks(self, query: str, chunks: Iterable[RetrievedChunk]) -> List[RetrievedChunk]:
        tokens = query.lower().split()
        scored: List[RetrievedChunk] = []
        for chunk in chunks:
            text_lower = chunk.text.lower()
            keyword_hits = sum(text_lower.count(token) for token in tokens)
            dense_score = self._simple_dense_sim(query, chunk.text)
            final_score = self.config.weights.bm25_weight * keyword_hits + self.config.weights.dense_weight * dense_score
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    source_type=chunk.source_type,
                    score=float(final_score),
                    metadata=chunk.metadata,
                )
            )
        return scored

    def _simple_dense_sim(self, query: str, text: str) -> float:
        query_tokens = set(query.lower().split())
        text_tokens = set(text.lower().split())
        if not query_tokens or not text_tokens:
            return 0.0
        return len(query_tokens & text_tokens) / len(query_tokens | text_tokens)

    def _fuse_results(
        self,
        intent: str,
        fact_results: List[RetrievedChunk],
        example_results: List[RetrievedChunk],
    ) -> List[RetrievedChunk]:
        weight_fact = self.config.weights.fact_weight
        weight_example = self.config.weights.example_weight

        if intent in {"factual", "fact"}:
            weight_example *= 0.5
        elif intent in {"experiential", "example"}:
            weight_fact *= 0.5

        combined: Dict[str, RetrievedChunk] = {}
        for result in fact_results:
            combined[result.chunk_id] = result
            combined[result.chunk_id].score *= weight_fact

        for result in example_results:
            if result.chunk_id in combined:
                combined[result.chunk_id].score += result.score * weight_example
            else:
                combined[result.chunk_id] = RetrievedChunk(
                    chunk_id=result.chunk_id,
                    text=result.text,
                    source_type=result.source_type,
                    score=result.score * weight_example,
                    metadata=result.metadata,
                )

        return list(combined.values())
