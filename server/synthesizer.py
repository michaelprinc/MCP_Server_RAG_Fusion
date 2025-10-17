"""Context synthesizer for retrieved chunks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .models import RetrievedChunk


@dataclass(slots=True)
class SynthesizerConfig:
    include_citations: bool = True


class ContextSynthesizer:
    """Builds structured context blocks with clear provenance."""

    def __init__(self, config: SynthesizerConfig | None = None) -> None:
        self.config = config or SynthesizerConfig()

    def build_context(self, chunks: Iterable[RetrievedChunk]) -> str:
        factual: List[str] = []
        experiential: List[str] = []

        for chunk in chunks:
            formatted = self._format_chunk(chunk)
            if chunk.source_type == "fact":
                factual.append(formatted)
            else:
                experiential.append(formatted)

        parts: List[str] = ["<RETRIEVAL_CONTEXT>"]
        if factual:
            parts.append("  <FACTUAL_KNOWLEDGE source=\"authoritative\">")
            parts.extend(f"    {line}" for line in factual)
            parts.append("  </FACTUAL_KNOWLEDGE>")
        if experiential:
            parts.append("  <EXPERIENTIAL_KNOWLEDGE source=\"practical\">")
            parts.extend(f"    {line}" for line in experiential)
            parts.append("  </EXPERIENTIAL_KNOWLEDGE>")
        parts.append("</RETRIEVAL_CONTEXT>")
        return "\n".join(parts)

    def _format_chunk(self, chunk: RetrievedChunk) -> str:
        citation = ""
        if self.config.include_citations:
            source = chunk.metadata.get("section") or chunk.metadata.get("source") or "unknown"
            citation = f" [Source: {source}]"
        text = chunk.text.strip().replace("\n", " ")
        return f"<chunk id=\"{chunk.chunk_id}\" confidence=\"{chunk.score:.2f}\">{text}{citation}</chunk>"
