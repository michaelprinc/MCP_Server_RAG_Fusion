# Troubleshooting Guide

## Indexer Issues

- **Symptom:** Index build aborts mid-run.  
  **Checks:** Review `indexer` logs for OCR or PDF parsing errors. Inspect artifact quarantine folder in `data\artifacts\quarantine`.  
  **Resolution:** Enable verbose logging via `--log-level DEBUG`, isolate problematic PDF pages with the `--page-range` flag, or fallback to image-only OCR.

- **Symptom:** Excessive memory usage.  
  **Checks:** Verify chunking parameters; large chunk sizes increase embedding footprint.  
  **Resolution:** Reduce `CHUNK_SIZE`, process PDFs page-by-page, and ensure temporary images are deleted after processing.

## Server Issues

- **Symptom:** `/health` returns 500.  
  **Checks:** Confirm `manifest.json` is well-formed and index files exist.  
  **Resolution:** Rebuild indexes, clear cache directory, and restart the container.

- **Symptom:** Slow responses (>500 ms).  
  **Checks:** Inspect `fusion` weights, verify FAISS index type, and check CPU load.  
  **Resolution:** Enable caching, switch to IVF_PQ for large datasets, or warm cache with frequent queries.

- **Symptom:** Missing citations in responses.  
  **Checks:** Ensure each chunk contains `source` metadata; reranker should not drop metadata fields.  
  **Resolution:** Patch `synthesizer` templates to enforce fallback citation placeholders.

## MCP Integration

- **Symptom:** MCP client rejects tool manifest.  
  **Checks:** Validate `configs\mcp-tools.json` against JSON schema.  
  **Resolution:** Use `python -m json.tool configs\mcp-tools.json` for validation before deployment.

- **Symptom:** `open_pdf_page` returns inaccessible URI.  
  **Checks:** Confirm PDFs are exposed via permissible scheme (e.g., `file://` or signed URL).  
  **Resolution:** Update handler to return MCP resource streams when direct file access is not available.

## Windows PowerShell Tips

- Use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` if script execution is required temporarily.
- When working with long-running Docker commands, prefer `Start-Job` to avoid blocking interactive shells.
