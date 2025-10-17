"""Pipeline orchestration for index builds."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

import numpy as np

from .build_bm25 import BM25BuildConfig, build_bm25_index
from .build_faiss import FaissBuildConfig, build_faiss_index
from .chunk import ChunkConfig, chunk_documents
from .embed import EmbeddingConfig, EmbeddingGenerator
from .ingest import DocumentIngestor, IngestConfig
from .utils import DocumentChunk, ensure_directory, save_jsonl, split_chunks_by_source

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IndexBuildConfig:
    input_dir: Path
    output_dir: Path
    artifacts_dir: Path
    manifest_name: str = "manifest.json"
    source_type: str = "fact"
    ocr_languages: str = "eng"
    chunk_size: int = 512
    chunk_overlap: int = 50
    embedding_model: str = "BAAI/bge-m3"
    faiss_index_type: str = "IVF_PQ"
    faiss_nlist: int = 100
    faiss_m: int = 8
    faiss_nbits: int = 8

    def validate(self) -> None:
        if self.source_type not in {"fact", "example"}:
            raise ValueError(f"Unsupported source type: {self.source_type}")


@dataclass(slots=True)
class IndexBuildResult:
    manifest_path: Path
    total_chunks: int
    fact_chunks: int
    example_chunks: int


class IndexPipeline:
    """Main orchestration entry point for index builds."""

    def __init__(self, config: IndexBuildConfig) -> None:
        self.config = config
        self.config.validate()

    def run(self) -> IndexBuildResult:
        logger.info("Starting index build with config: %s", self.config)

        ingestor = DocumentIngestor(
            IngestConfig(
                ocr_languages=self.config.ocr_languages,
                artifacts_dir=self.config.artifacts_dir,
            )
        )
        chunked: List[DocumentChunk] = []

        for pdf_path in sorted(self.config.input_dir.glob("*.pdf")):
            for raw_chunk in ingestor.ingest(pdf_path, source_type=self.config.source_type):
                chunked.extend(self._chunk(raw_chunk))

        text_chunks = [chunk for chunk in chunked if chunk.content_type == "text"]
        embeddings = list(self._embed(text_chunks))

        chunk_groups = split_chunks_by_source(chunked)
        ensure_directory(self.config.output_dir)

        manifest_components: Dict[str, str] = {}

        for key, group in chunk_groups.items():
            if not group:
                continue
            bm25_path = self.config.output_dir / f"{key}_bm25.pkl"
            build_bm25_index(group, BM25BuildConfig(output_path=bm25_path))
            manifest_components[f"{key}_bm25"] = bm25_path.name

        if embeddings:
            faiss_path = self.config.output_dir / f"{self.config.source_type}_faiss.index"
            build_faiss_index(
                embeddings,
                FaissBuildConfig(
                    output_path=faiss_path,
                    index_type=self.config.faiss_index_type,
                    nlist=self.config.faiss_nlist,
                    m=self.config.faiss_m,
                    nbits=self.config.faiss_nbits,
                ),
            )
            manifest_components[f"{self.config.source_type}_faiss"] = faiss_path.name

        chunks_path = self.config.output_dir / f"chunks_{self.config.source_type}.jsonl"
        save_jsonl(chunks_path, (chunk.to_json() for chunk in chunked))
        manifest_components["chunks"] = chunks_path.name

        manifest = self._write_manifest(manifest_components, len(chunked), chunk_groups)
        logger.info("Index build complete. Manifest at %s", manifest)

        return IndexBuildResult(
            manifest_path=manifest,
            total_chunks=len(chunked),
            fact_chunks=len(chunk_groups.get("fact", [])),
            example_chunks=len(chunk_groups.get("example", [])),
        )

    def _chunk(self, chunk: DocumentChunk) -> Iterator[DocumentChunk]:
        chunker_config = ChunkConfig(max_tokens=self.config.chunk_size, overlap=self.config.chunk_overlap)
        yield from chunk_documents([chunk], chunker_config)

    def _embed(self, chunks: Iterable[DocumentChunk]) -> Iterator[Tuple[DocumentChunk, np.ndarray]]:
        embedder = EmbeddingGenerator(
            EmbeddingConfig(
                model_name=self.config.embedding_model,
            )
        )
        yield from embedder.encode(chunks)

    def _write_manifest(
        self,
        components: Dict[str, str],
        total_chunks: int,
        chunk_groups: Dict[str, List[DocumentChunk]],
    ) -> Path:
        manifest_path = self.config.output_dir / self.config.manifest_name
        existing = {}
        if manifest_path.exists():
            with manifest_path.open("r", encoding="utf-8") as handle:
                existing = json.load(handle)

        previous_stats = existing.get("statistics", {})
        fact_chunks = previous_stats.get("fact_chunks", 0)
        example_chunks = previous_stats.get("example_chunks", 0)

        if self.config.source_type == "fact":
            fact_chunks = len(chunk_groups.get("fact", []))
        elif self.config.source_type == "example":
            example_chunks = len(chunk_groups.get("example", []))

        payload = {
            "version": datetime.now(timezone.utc).strftime("v%Y%m%d%H%M%S"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "components": {**existing.get("components", {}), **components},
            "statistics": {
                "total_chunks": fact_chunks + example_chunks,
                "fact_chunks": fact_chunks,
                "example_chunks": example_chunks,
            },
        }
        with manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return manifest_path
