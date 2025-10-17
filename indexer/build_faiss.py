"""FAISS index construction utilities."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import faiss
import numpy as np

from .utils import DocumentChunk, ensure_directory

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FaissBuildConfig:
    output_path: Path
    index_type: str = "IVF_PQ"
    nlist: int = 100
    m: int = 8
    nbits: int = 8


def build_faiss_index(
    embeddings: Iterable[Tuple[DocumentChunk, np.ndarray]],
    config: FaissBuildConfig,
) -> Path:
    chunk_ids: List[str] = []
    vectors: List[np.ndarray] = []

    for chunk, vector in embeddings:
        chunk_ids.append(chunk.chunk_id)
        vectors.append(vector.astype("float32"))

    if not vectors:
        raise ValueError("No embeddings provided for FAISS index build.")

    matrix = np.vstack(vectors)
    dimension = matrix.shape[1]
    index = _create_index(dimension, config, len(vectors))
    index = _train_index(index, matrix, config)
    index.add(matrix)

    ensure_directory(config.output_path.parent)
    faiss.write_index(index, str(config.output_path))

    ids_path = config.output_path.with_suffix(".ids.txt")
    with ids_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(chunk_ids))

    meta_path = config.output_path.with_suffix(".meta.json")
    ensure_directory(meta_path.parent)
    metadata = {
        "dimension": dimension,
        "index_type": config.index_type,
        "vector_count": len(chunk_ids),
    }
    with meta_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle)

    logger.info("Wrote FAISS index to %s", config.output_path)
    return config.output_path


def _create_index(dimension: int, config: FaissBuildConfig, n_vectors: int) -> faiss.Index:
    if config.index_type.upper() == "FLAT" or n_vectors < 10_000:
        logger.info("Using IndexFlatIP for %s vectors", n_vectors)
        return faiss.IndexFlatIP(dimension)

    nlist = config.nlist or int(np.sqrt(n_vectors))
    quantizer = faiss.IndexFlatIP(dimension)
    index = faiss.IndexIVFPQ(quantizer, dimension, nlist, config.m, config.nbits)
    return index


def _train_index(index: faiss.Index, matrix: np.ndarray, config: FaissBuildConfig) -> faiss.Index:
    if index.is_trained:
        return index

    sample_size = min(100_000, matrix.shape[0])
    sample = matrix[np.random.choice(matrix.shape[0], sample_size, replace=False)]
    logger.info("Training FAISS index on %s samples", sample_size)
    index.train(sample)
    return index
