"""Command line interface for the indexer container."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .pipeline import IndexBuildConfig, IndexPipeline

app = typer.Typer(help="Dual-index RAG ingestion utilities.")
console = Console()


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


@app.command()
def build(
    input: Path = typer.Option(Path("data/pdf"), "--input", "-i", exists=True, file_okay=False),
    output: Path = typer.Option(Path("data/indexes"), "--output", "-o"),
    artifacts: Path = typer.Option(Path("data/artifacts"), "--artifacts"),
    source_type: str = typer.Option("fact", "--source-type", case_sensitive=False),
    chunk_size: int = typer.Option(512, "--chunk-size"),
    chunk_overlap: int = typer.Option(50, "--chunk-overlap"),
    embedding_model: str = typer.Option("BAAI/bge-m3", "--embedding-model"),
    ocr_languages: str = typer.Option("eng", "--ocr-languages"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Build indexes from PDFs using the configured pipeline."""
    configure_logging(verbose)
    config = IndexBuildConfig(
        input_dir=input,
        output_dir=output,
        artifacts_dir=artifacts,
        source_type=source_type.lower(),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        embedding_model=embedding_model,
        ocr_languages=ocr_languages,
    )
    pipeline = IndexPipeline(config)
    result = pipeline.run()
    _display_summary(result.manifest_path)


@app.command()
def show_manifest(path: Path = typer.Argument(Path("data/indexes/manifest.json"))) -> None:
    """Pretty print a manifest file for quick inspection."""
    with path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    table = Table(title="Index Manifest")
    table.add_column("Key")
    table.add_column("Value")
    for key, value in manifest.items():
        table.add_row(str(key), json.dumps(value, indent=2) if isinstance(value, dict) else str(value))
    console.print(table)


def _display_summary(manifest_path: Path) -> None:
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    stats = manifest.get("statistics", {})
    console.print(f"[green]Index build completed.[/green] Manifest: {manifest_path}")
    console.print(f"Total chunks: {stats.get('total_chunks', 0)}")
    console.print(f"Fact chunks: {stats.get('fact_chunks', 0)}")
    console.print(f"Example chunks: {stats.get('example_chunks', 0)}")


if __name__ == "__main__":
    app()
