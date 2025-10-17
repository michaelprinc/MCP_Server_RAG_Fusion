# RAG-Fusion MCP Server

This repository implements a production-oriented dual-index Retrieval Augmented Generation (RAG) system tailored for Model Context Protocol (MCP) integrations. The architecture separates authoritative factual knowledge from experiential usage examples, enabling fused responses that combine precision with real-world insights.

## Repository Layout

```
rag-fusion-mcp/
├── configs/                # Runtime configuration sources (models, MCP tools, env templates)
├── data/                   # Persistent volume root (pdf, artifacts, indexes)
├── docker/                 # Container build assets
├── docs/                   # Operational and configuration documentation
├── indexer/                # Ad-hoc indexing pipeline
├── server/                 # Persistent MCP server
├── tests/                  # Automated evaluation suites
├── docker-compose.yml      # Orchestration for indexer + server
├── pyproject.toml          # Project metadata and tooling configuration
└── requirements.txt        # Shared Python dependencies
```

## Quick Start (Windows PowerShell Friendly)

```powershell
# 1. Create virtual environment (optional but recommended)
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run indexer pipeline locally (dry-run)
python -m indexer.cli build --input data\pdf --output data\indexes

# 4. Launch MCP server (development)
uvicorn server.app:app --host 0.0.0.0 --port 8080 --reload
```

Docker usage is documented in `docs/OPERATIONS.md`. All management commands are compatible with Windows PowerShell shells.

## Status

- ✅ Repository scaffolding
- ✅ Configuration templates
- ✅ Indexer & server skeletons with detailed docstrings
- ☐ Full PDF ingestion implementation
- ☐ End-to-end retrieval fusion
- ☐ Evaluation dataset population

Follow the phase-based checklist in `docs/OPERATIONS.md` to move from scaffolding to production readiness.
