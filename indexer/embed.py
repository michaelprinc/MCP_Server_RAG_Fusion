"""Embedding generation for textual and image content."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    from sentence_transformers import util as st_utils
except ImportError:
    st_utils = None  # type: ignore

from .utils import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EmbeddingConfig:
    model_name: str = "BAAI/bge-m3"
    batch_size: int = 32
    device: str = "cpu"
    normalize: bool = True
    cache_dir: Optional[Path] = None
    image_model_name: Optional[str] = None


class EmbeddingGenerator:
    """Wrapper around SentenceTransformer for batched embeddings."""

    def __init__(self, config: Optional[EmbeddingConfig] = None) -> None:
        self.config = config or EmbeddingConfig()
        self.model = SentenceTransformer(self.config.model_name, device=self.config.device)
        if self.config.cache_dir:
            self.model.save(str(self.config.cache_dir))

    def encode(self, chunks: Iterable[DocumentChunk]) -> Iterator[Tuple[DocumentChunk, np.ndarray]]:
        buffer: List[DocumentChunk] = []
        for chunk in chunks:
            if chunk.content_type != "text":
                continue
            buffer.append(chunk)
            if len(buffer) >= self.config.batch_size:
                yield from self._encode_buffer(buffer)
                buffer = []

        if buffer:
            yield from self._encode_buffer(buffer)

    def _encode_buffer(self, buffer: List[DocumentChunk]) -> Iterator[Tuple[DocumentChunk, np.ndarray]]:
        texts = [chunk.text for chunk in buffer]
        embeddings = self.model.encode(texts, batch_size=self.config.batch_size, convert_to_numpy=True, normalize_embeddings=self.config.normalize)
        for chunk, embedding in zip(buffer, embeddings, strict=True):
            yield chunk, embedding
