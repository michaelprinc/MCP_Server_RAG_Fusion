"""Layout aware chunking utilities."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Sequence

from .utils import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChunkConfig:
    max_tokens: int = 512
    overlap: int = 50
    separators: Sequence[str] = ("\n\n", "\n", ". ", " ")


class Chunker:
    """Splits extracted text into semantically coherent chunks."""

    def __init__(self, config: ChunkConfig | None = None) -> None:
        self.config = config or ChunkConfig()

    def chunk(self, chunk: DocumentChunk) -> Iterator[DocumentChunk]:
        if chunk.content_type != "text":
            yield chunk
            return

        sentences = self._split_text(chunk.text)
        current_text: List[str] = []
        current_length = 0
        token_budget = self.config.max_tokens
        overlap_tokens = self.config.overlap
        chunk_index = 0
        cached_tokens: List[str] = []

        for sentence in sentences:
            sentence_tokens = sentence.split()
            token_count = len(sentence_tokens)
            if current_length + token_count > token_budget and current_text:
                yield self._emit_chunk(chunk, chunk_index, current_text)
                chunk_index += 1
                cached_tokens = current_text[-overlap_tokens:] if overlap_tokens > 0 else []
                current_text = cached_tokens.copy()
                current_length = len(" ".join(current_text).split())

            current_text.append(sentence)
            current_length += token_count

        if current_text:
            yield self._emit_chunk(chunk, chunk_index, current_text)

    def _emit_chunk(self, base_chunk: DocumentChunk, index: int, segments: List[str]) -> DocumentChunk:
        new_chunk = DocumentChunk(
            chunk_id=f"{base_chunk.chunk_id}_chunk{index:03d}",
            document_id=base_chunk.document_id,
            page=base_chunk.page,
            text=" ".join(segments).strip(),
            content_type=base_chunk.content_type,
            source_type=base_chunk.source_type,
            metadata={**base_chunk.metadata, "parent_chunk": base_chunk.chunk_id},
        )
        logger.debug("Created derived chunk %s", new_chunk.chunk_id)
        return new_chunk

    def _split_text(self, text: str) -> List[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []
        sentences = [normalized]
        for separator in self.config.separators:
            temp: List[str] = []
            for segment in sentences:
                if separator in segment:
                    temp.extend([part.strip() for part in segment.split(separator) if part.strip()])
                else:
                    temp.append(segment)
            sentences = temp
        return sentences


def chunk_documents(chunks: Iterable[DocumentChunk], config: ChunkConfig | None = None) -> Iterator[DocumentChunk]:
    chunker = Chunker(config)
    for chunk in chunks:
        yield from chunker.chunk(chunk)
