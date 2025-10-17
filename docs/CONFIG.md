# Configuration Guide

This document summarizes the configuration artifacts used by the dual-index RAG fusion system.

## Environment Variables

Environment variables can be supplied through Docker Compose, `.env` files, or direct PowerShell exports.

| Variable | Description | Default |
| --- | --- | --- |
| `PDF_DIR` | Location of input PDFs for the indexer | `data/pdf` |
| `ARTIFACTS_DIR` | Intermediate artifact output directory | `data/artifacts` |
| `INDEX_DIR` | Target directory for built indexes | `data/indexes` |
| `OCR_LANGUAGES` | Tesseract language packs to enable | `eng` |
| `EMBEDDING_MODEL` | Text embedding model identifier | `BAAI/bge-m3` |
| `PORT` | MCP server HTTP port | `8080` |
| `MODEL_CONFIG` | Path to `model-config.yml` | `configs/model-config.yml` |
| `MCP_TOOLS` | Path to `mcp-tools.json` | `configs/mcp-tools.json` |
| `ROUTER_MODE` | `classifier` or `mini-llm` | `classifier` |
| `CACHE_SIZE` | Maximum query cache entries | `1000` |

## `configs/model-config.yml`

- Defines embedding, retrieval, reranking, and router options.
- Supports toggling image embeddings (`embeddings.image.enabled`) for multimodal indexing.
- Adjust `retrieval.fusion` weights to tune factual vs experiential emphasis.
- Reranker, router, and caching sections provide central tuning for runtime deployment.

## `configs/mcp-tools.json`

- Exposes MCP tools used by Copilot or other MCP clients.
- Update parameter schema to reflect runtime query requirements.
- Resources advertise the resolvable URI formats for downstream clients.

## Secrets Handling

- Sensitive values can be supplied through Docker secrets.
- `configs/server.env` is a template and should not be committed once populated with secrets.
- When using Docker Compose, define secrets in `docker-compose.yml` under the `secrets` section.

## Windows PowerShell Notes

- Use `Set-Item -Path Env:PORT -Value 8080` to set environment variables for the current session.
- To persist local overrides, copy `configs/server.env` to `.env` and fill in the values. PowerShell compatible commands are documented in `docs/OPERATIONS.md`.
