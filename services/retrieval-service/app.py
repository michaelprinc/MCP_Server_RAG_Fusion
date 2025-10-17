"""Retrieval Service - Core RAG-Fusion Engine.

This service handles:
- Index loading (FAISS + BM25)
- Query routing and intent classification
- Multi-strategy retrieval
- Reranking and fusion
- Context synthesis
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import from parent server module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.retriever import Retriever, RetrievalConfig
from server.fusion import Reranker, RerankConfig
from server.router import QueryRouter, RouterConfig
from server.synthesizer import ContextSynthesizer, SynthesizerConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [RetrievalService] %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API
class RetrievalRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(10, ge=1, le=100, description="Number of results")
    intent: Optional[str] = Field(None, description="Query intent (auto-classified if None)")
    include_context: bool = Field(True, description="Whether to synthesize context")
    min_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Minimum confidence threshold")


class ChunkResult(BaseModel):
    chunk_id: str
    text: str
    score: float
    source: str
    metadata: Dict[str, Any]


class RetrievalResponse(BaseModel):
    chunks: List[ChunkResult]
    context: Optional[str] = None
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: int
    index_version: str
    indexes_loaded: bool


# FastAPI app
app = FastAPI(
    title="RAG-Fusion Retrieval Service",
    description="Microservice for multi-strategy retrieval and fusion",
    version="1.0.0",
)

# CORS middleware for cross-service communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
APP_START_TIME = time.time()
retriever: Optional[Retriever] = None
reranker: Optional[Reranker] = None
router: Optional[QueryRouter] = None
synthesizer: Optional[ContextSynthesizer] = None
INDEX_VERSION = "unknown"


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize retrieval components."""
    global retriever, reranker, router, synthesizer, INDEX_VERSION
    
    logger.info("Starting Retrieval Service...")
    
    # Load configuration from environment
    index_dir = Path(os.getenv("INDEX_DIR", "/data/indexes"))
    router_mode = os.getenv("ROUTER_MODE", "classifier")
    
    logger.info(f"Loading indexes from: {index_dir}")
    logger.info(f"Router mode: {router_mode}")
    
    try:
        # Initialize components
        retriever = Retriever(RetrievalConfig(index_dir=index_dir))
        reranker = Reranker(RerankConfig())
        router = QueryRouter(RouterConfig(mode=router_mode))
        synthesizer = ContextSynthesizer(SynthesizerConfig())
        
        INDEX_VERSION = retriever.index_version
        
        logger.info(f"✓ Retrieval Service initialized successfully")
        logger.info(f"  Index version: {INDEX_VERSION}")
        logger.info(f"  Retriever ready: {retriever is not None}")
        logger.info(f"  Reranker ready: {reranker is not None}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Retrieval Service: {e}", exc_info=True)
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    uptime = int(time.time() - APP_START_TIME)
    indexes_loaded = retriever is not None
    
    status = "healthy" if indexes_loaded else "unhealthy"
    
    return HealthResponse(
        status=status,
        service="retrieval-service",
        version="1.0.0",
        uptime_seconds=uptime,
        index_version=INDEX_VERSION,
        indexes_loaded=indexes_loaded,
    )


@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_chunks(request: RetrievalRequest) -> RetrievalResponse:
    """
    Retrieve and rerank chunks using RAG-Fusion pipeline.
    
    Pipeline:
    1. Query routing (intent classification)
    2. Multi-strategy retrieval (FAISS + BM25)
    3. Reciprocal rank fusion
    4. Cross-encoder reranking
    5. Context synthesis (optional)
    """
    if retriever is None or reranker is None or router is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    start_time = time.time()
    
    try:
        # Step 1: Classify intent if not provided
        intent = request.intent or router.classify(request.query)
        logger.info(f"Query intent: {intent} for query: {request.query[:50]}...")
        
        # Step 2: Retrieve candidates
        candidates = retriever.retrieve(
            query=request.query,
            intent=intent,
            top_k=max(request.top_k * 2, 20),  # Retrieve more for reranking
        )
        logger.info(f"Retrieved {len(candidates)} candidates")
        
        # Step 3: Rerank with cross-encoder
        reranked = reranker.rerank(
            query=request.query,
            chunks=candidates,
            top_k=request.top_k,
        )
        logger.info(f"Reranked to top {len(reranked)} chunks")
        
        # Step 4: Filter by confidence
        filtered = [c for c in reranked if c.score >= request.min_confidence]
        logger.info(f"Filtered to {len(filtered)} chunks (min_conf={request.min_confidence})")
        
        # Step 5: Synthesize context (optional)
        context = None
        if request.include_context and synthesizer is not None:
            context = synthesizer.build_context(filtered)
        
        # Convert to response format
        chunk_results = [
            ChunkResult(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                score=chunk.score,
                source=chunk.source,
                metadata=chunk.metadata,
            )
            for chunk in filtered
        ]
        
        retrieval_time_ms = int((time.time() - start_time) * 1000)
        
        return RetrievalResponse(
            chunks=chunk_results,
            context=context,
            metadata={
                "intent": intent,
                "retrieval_time_ms": retrieval_time_ms,
                "candidates_retrieved": len(candidates),
                "chunks_reranked": len(reranked),
                "chunks_returned": len(filtered),
                "index_version": INDEX_VERSION,
            },
        )
        
    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")


@app.get("/indexes")
async def list_indexes() -> Dict[str, Any]:
    """List available indexes and their metadata."""
    if retriever is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "index_version": INDEX_VERSION,
        "index_dir": str(retriever.config.index_dir),
        "sources": retriever.get_available_sources() if hasattr(retriever, 'get_available_sources') else ["fact"],
    }


@app.post("/classify")
async def classify_query(query: str) -> Dict[str, str]:
    """Classify query intent."""
    if router is None:
        raise HTTPException(status_code=503, detail="Router not initialized")
    
    intent = router.classify(query)
    return {"query": query, "intent": intent}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8081"))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
    )
