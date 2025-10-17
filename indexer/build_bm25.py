"""BM25 index construction."""

from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from rank_bm25 import BM25Okapi

from .utils import DocumentChunk, ensure_directory

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BM25BuildConfig:
    output_path: Path
    k1: float = 1.5
    b: float = 0.75


def build_bm25_index(chunks: Iterable[DocumentChunk], config: BM25BuildConfig) -> Path:
    documents: List[Sequence[str]] = []
    chunk_ids: List[str] = []

    for chunk in chunks:
        if chunk.content_type != "text":
            continue
        tokens = chunk.text.split()
        documents.append(tokens)
        chunk_ids.append(chunk.chunk_id)

    bm25 = BM25Okapi(documents, k1=config.k1, b=config.b)
    payload = {
        "bm25": bm25,
        "chunk_ids": chunk_ids,
    }

    ensure_directory(config.output_path.parent)
    with config.output_path.open("wb") as handle:
        pickle.dump(payload, handle)

    logger.info("Wrote BM25 index to %s", config.output_path)
    return config.output_path
