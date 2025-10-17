"""Unit tests for retrieval fusion logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.models import RetrievedChunk
from server.retriever import IndexStore, RetrievalConfig, Retriever


class StubStore(IndexStore):
    def __init__(self) -> None:
        self.index_dir = Path(".")
        self.fact_chunks = [
            RetrievedChunk(
                chunk_id="fact_1",
                text="Manual step describing procedure.",
                source_type="fact",
                score=0.9,
                metadata={"section": "1.1"},
            )
        ]
        self.example_chunks = [
            RetrievedChunk(
                chunk_id="example_1",
                text="Example scenario from field use.",
                source_type="example",
                score=0.7,
                metadata={"scenario": "field"},
            )
        ]
        self.chunk_lookup = {chunk.chunk_id: chunk for chunk in self.fact_chunks + self.example_chunks}
        self.index_version = "test"


class DummyRetriever(Retriever):
    def __init__(self) -> None:
        super().__init__(RetrievalConfig())
        self.store = StubStore()


def test_factual_intent_prioritizes_fact_chunks() -> None:
    retriever = DummyRetriever()
    results = retriever.retrieve(query="procedure", intent="factual", top_k=2)
    assert results[0].source_type == "fact"


def test_experiential_intent_includes_examples() -> None:
    retriever = DummyRetriever()
    results = retriever.retrieve(query="example field", intent="experiential", top_k=2)
    chunk_ids = {chunk.chunk_id for chunk in results}
    assert "example_1" in chunk_ids


def test_unknown_intent_raises_error() -> None:
    retriever = DummyRetriever()
    with pytest.raises(ValueError):
        retriever.retrieve(query="test", intent="invalid", top_k=1)
