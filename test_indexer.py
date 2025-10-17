#!/usr/bin/env python3
"""Test script to process the PDF and build indexes."""

import logging
from pathlib import Path

from indexer.pipeline import IndexBuildConfig, IndexPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

def main():
    """Run the indexing pipeline."""
    config = IndexBuildConfig(
        input_dir=Path("data/pdf"),
        output_dir=Path("data/indexes"),
        artifacts_dir=Path("data/artifacts"),
        source_type="fact",
        chunk_size=256,
        chunk_overlap=25,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        ocr_languages="eng",
    )
    
    pipeline = IndexPipeline(config)
    try:
        result = pipeline.run()
        print(f"✅ Index build completed!")
        print(f"📄 Manifest: {result.manifest_path}")
        print(f"📊 Total chunks: {result.total_chunks}")
        print(f"📚 Fact chunks: {result.fact_chunks}")
        print(f"💡 Example chunks: {result.example_chunks}")
    except Exception as e:
        print(f"❌ Error during indexing: {e}")
        raise

if __name__ == "__main__":
    main()