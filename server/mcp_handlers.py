"""MCP handler implementations."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from cachetools import LRUCache
from fastapi import APIRouter, HTTPException

from .fusion import RerankConfig, Reranker
from .models import (
    ChunkDetailsRequest,
    ChunkDetailsResponse,
    IndexListResponse,
    OpenPdfPageRequest,
    OpenPdfPageResponse,
    SearchRequest,
    SearchResponse,
    RetrievedChunk,
)
from .retriever import RetrievalConfig, Retriever
from .router import QueryRouter, RouterConfig
from .synthesizer import ContextSynthesizer, SynthesizerConfig

logger = logging.getLogger(__name__)


@dataclass
class ServerState:
    retriever: Retriever
    reranker: Reranker
    router: QueryRouter
    synthesizer: ContextSynthesizer
    index_dir: Path
    cache: LRUCache[str, List[Dict[str, object]]]

    @property
    def index_version(self) -> str:
        return self.retriever.index_version


def build_state(config: Dict[str, str]) -> ServerState:
    index_dir = Path(config.get("INDEX_DIR", "data/indexes"))
    cache_size = int(config.get("CACHE_SIZE", "1000"))

    retriever = Retriever(RetrievalConfig(index_dir=index_dir))
    reranker = Reranker(RerankConfig())
    router = QueryRouter(RouterConfig(mode=config.get("ROUTER_MODE", "classifier")))
    synthesizer = ContextSynthesizer(SynthesizerConfig())
    cache: LRUCache[str, List[Dict[str, object]]] = LRUCache(maxsize=cache_size)

    return ServerState(
        retriever=retriever,
        reranker=reranker,
        router=router,
        synthesizer=synthesizer,
        index_dir=index_dir,
        cache=cache,
    )


def register_routes(router: APIRouter, state: ServerState) -> None:
    @router.post("/search_manual", response_model=SearchResponse)
    async def search_manual(request: SearchRequest) -> SearchResponse:
        cache_key = f"{request.query}:{request.top_k}:{request.include_examples}:{request.min_confidence}"
        if cache_key in state.cache:
            cached = state.cache[cache_key]
            return SearchResponse(
                context=_render_context(cached, state),
                chunks=cached,
                metadata={
                    "intent": "cached",
                    "index_version": state.index_version,
                },
            )

        intent = state.router.classify(request.query)
        candidates = state.retriever.retrieve(
            query=request.query,
            intent=intent,
            top_k=max(request.top_k, state.retriever.config.top_k_initial),
        )
        reranked = state.reranker.rerank(request.query, candidates, top_k=request.top_k)
        context = state.synthesizer.build_context(reranked)
        payload = [chunk.to_dict() for chunk in reranked]
        state.cache[cache_key] = payload
        return SearchResponse(
            context=context,
            chunks=payload,
            metadata={
                "intent": intent,
                "retrieval_time_ms": 0,
                "index_version": state.index_version,
            },
        )

    @router.post("/get_chunk_details", response_model=ChunkDetailsResponse)
    async def get_chunk_details(request: ChunkDetailsRequest) -> ChunkDetailsResponse:
        if not request.chunk_ids:
            raise HTTPException(status_code=400, detail="chunk_ids cannot be empty.")
        chunks = state.retriever.chunks_by_id(request.chunk_ids)
        return ChunkDetailsResponse(chunks=[chunk.to_dict() for chunk in chunks])

    @router.post("/open_pdf_page", response_model=OpenPdfPageResponse)
    async def open_pdf_page(request: OpenPdfPageRequest) -> OpenPdfPageResponse:
        pdf_dir = state.index_dir.parent / "pdf"
        pdf_path = pdf_dir / f"{request.document_id}.pdf"
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="Document not found.")
        uri = pdf_path.resolve().as_uri() + f"#page={request.page}"
        return OpenPdfPageResponse(uri=uri)

    @router.get("/list_indexed_documents", response_model=IndexListResponse)
    async def list_indexed_documents() -> IndexListResponse:
        manifest_path = state.index_dir / "manifest.json"
        if not manifest_path.exists():
            return IndexListResponse(documents=[])
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
        stats = manifest.get("statistics", {})
        documents = [
            {
                "version": manifest.get("version"),
                "created_at": manifest.get("created_at"),
                "total_chunks": stats.get("total_chunks", 0),
                "fact_chunks": stats.get("fact_chunks", 0),
                "example_chunks": stats.get("example_chunks", 0),
            }
        ]
        return IndexListResponse(documents=documents)


def _render_context(chunks: List[Dict[str, object]], state: ServerState) -> str:
    reconstructed = [
        RetrievedChunk(
            chunk_id=chunk["chunk_id"],
            text=chunk["text"],
            source_type=chunk["source_type"],
            score=float(chunk.get("score", 0)),
            metadata=chunk.get("metadata", {}),
        )
        for chunk in chunks
    ]
    return state.synthesizer.build_context(reconstructed)
