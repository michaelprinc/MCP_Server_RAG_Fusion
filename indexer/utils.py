"""Utility helpers and data models for the indexing pipeline."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DocumentMetadata:
    document_id: str
    source_path: Path
    sha256: str
    total_pages: int
    version: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    page: int
    text: str
    content_type: str
    source_type: str  # "fact" or "example"
    metadata: Dict[str, object] = field(default_factory=dict)
    score: Optional[float] = None

    def to_json(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "chunk_id": self.chunk_id,
            "doc_id": self.document_id,
            "page": self.page,
            "content_type": self.content_type,
            "text": self.text,
            "source_type": self.source_type,
            "metadata": self.metadata,
        }
        if self.score is not None:
            payload["score"] = self.score
        return payload


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            sha.update(chunk)
    return f"sha256:{sha.hexdigest()}"


def save_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def slugify(value: str) -> str:
    allowed = []
    for char in value.lower():
        if char.isalnum():
            allowed.append(char)
        elif char in {" ", "-", "_"}:
            allowed.append("-")
    slug = "".join(allowed).strip("-")
    return "-".join(filter(None, slug.split("-")))


def split_chunks_by_source(chunks: Iterable[DocumentChunk]) -> Dict[str, List[DocumentChunk]]:
    groups: Dict[str, List[DocumentChunk]] = {"fact": [], "example": []}
    for chunk in chunks:
        key = chunk.source_type if chunk.source_type in groups else "fact"
        groups.setdefault(key, []).append(chunk)
    return groups
