"""PDF ingestion pipeline with OCR fallback and metadata capture."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

from .utils import DocumentChunk, DocumentMetadata, ensure_directory, hash_file, slugify

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestConfig:
    ocr_languages: str = "eng"
    artifacts_dir: Path = Path("data/artifacts")
    image_dpi: int = 300
    max_ocr_seconds: int = 30
    enable_tables: bool = True
    enable_images: bool = True


class DocumentIngestor:
    """Handles PDF ingestion and multimodal extraction."""

    def __init__(self, config: Optional[IngestConfig] = None) -> None:
        self.config = config or IngestConfig()

    def ingest(self, pdf_path: Path, source_type: str = "fact") -> Iterator[DocumentChunk]:
        metadata = self._build_metadata(pdf_path)
        logger.info("Ingesting %s", metadata.document_id)

        with fitz.open(pdf_path) as document:
            for page_index in range(document.page_count):
                page = document.load_page(page_index)
                text = page.get_text("text")
                if not text.strip():
                    text = self._perform_ocr(pdf_path, page_index)
                    extraction_method = "ocr"
                else:
                    extraction_method = "native"

                chunk_id = self._chunk_id(metadata.document_id, page_index, 0)
                yield DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=metadata.document_id,
                    page=page_index + 1,
                    text=text,
                    content_type="text",
                    source_type=source_type,
                    metadata={
                        "bbox": [0, 0, page.rect.width, page.rect.height],
                        "extraction_method": extraction_method,
                    },
                )

                if self.config.enable_images:
                    yield from self._extract_images(document, page_index, metadata.document_id, source_type)

        logger.info("Completed ingestion for %s", metadata.document_id)

    def _build_metadata(self, pdf_path: Path) -> DocumentMetadata:
        with fitz.open(pdf_path) as document:
            total_pages = document.page_count
        doc_id = slugify(pdf_path.stem)
        return DocumentMetadata(
            document_id=doc_id,
            source_path=pdf_path,
            sha256=hash_file(pdf_path),
            total_pages=total_pages,
        )

    def _perform_ocr(self, pdf_path: Path, page_index: int) -> str:
        try:
            images = convert_from_path(
                pdf_path,
                dpi=self.config.image_dpi,
                first_page=page_index + 1,
                last_page=page_index + 1,
            )
        except Exception as exc:
            logger.warning("Failed to rasterize page %s: %s", page_index + 1, exc)
            return ""

        if not images:
            return ""

        image: Image.Image = images[0]
        text = pytesseract.image_to_string(image, lang=self.config.ocr_languages)
        return text

    def _extract_images(
        self,
        document: fitz.Document,
        page_index: int,
        document_id: str,
        source_type: str,
    ) -> Iterable[DocumentChunk]:
        page = document.load_page(page_index)
        images: List = page.get_images(full=True)  # type: ignore[assignment]
        if not images:
            return []

        extracted_chunks: List[DocumentChunk] = []
        ensure_directory(self.config.artifacts_dir)

        for image_index, image_info in enumerate(images):
            xref = image_info[0]
            base_image = document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image.get("ext", "png")
            image_name = f"{document_id}_p{page_index + 1}_img{image_index}.{image_ext}"
            image_path = self.config.artifacts_dir / image_name
            with image_path.open("wb") as handle:
                handle.write(image_bytes)

            chunk_id = self._chunk_id(document_id, page_index, image_index + 1)
            extracted_chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    page=page_index + 1,
                    text="",
                    content_type="image",
                    source_type=source_type,
                    metadata={
                        "image_path": str(image_path),
                        "width": base_image.get("width"),
                        "height": base_image.get("height"),
                    },
                )
            )

        return extracted_chunks

    @staticmethod
    def _chunk_id(document_id: str, page_index: int, item_index: int) -> str:
        return f"{document_id}_p{page_index + 1:04d}_c{item_index:03d}"
