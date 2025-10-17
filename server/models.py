"""Shared data models for the MCP server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(10, ge=1, le=50)
    include_examples: bool = Field(True)
    min_confidence: float = Field(0.5, ge=0.0, le=1.0)

    @validator("query")
    def sanitize_query(cls, value: str) -> str:
        forbidden = ("<script>", "drop table", "--")
        lowered = value.lower()
        if any(pattern in lowered for pattern in forbidden):
            raise ValueError("Query contains forbidden patterns.")
        return value.strip()


class AdminReloadResponse(BaseModel):
    status: str
    index_version: str


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    source_type: str
    score: float
    metadata: Dict[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_type": self.source_type,
            "score": self.score,
            "metadata": self.metadata,
        }


class SearchResponse(BaseModel):
    context: str
    chunks: List[Dict[str, object]]
    metadata: Dict[str, object]


class ChunkDetailsRequest(BaseModel):
    chunk_ids: List[str]


class ChunkDetailsResponse(BaseModel):
    chunks: List[Dict[str, object]]


class OpenPdfPageRequest(BaseModel):
    document_id: str
    page: int = Field(..., ge=1)


class OpenPdfPageResponse(BaseModel):
    uri: str


class IndexListResponse(BaseModel):
    documents: List[Dict[str, object]]
