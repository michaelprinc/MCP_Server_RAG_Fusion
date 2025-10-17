# 🚀 RAG-Fusion MCP Server - Quick Start Guide

## Overview
This guide shows you how to use the RAG-Fusion MCP Server running in Docker to query the CI360 manual using advanced retrieval techniques.

## 📋 Prerequisites
- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)
- The CI360 manual indexes (already built in `data/indexes/`)

## 🐳 Docker Deployment

### Starting the Server

```bash
# Start the MCP server
docker compose up -d

# Check server status
docker compose ps

# View server logs
docker compose logs -f server
```

### Stopping the Server

```bash
# Stop the server
docker compose down

# Stop and remove all data
docker compose down -v
```

## 🔍 Using the MCP Server

### 1. Health Check

Check if the server is running:

```bash
# Using curl (Git Bash/WSL)
curl http://localhost:8080/health

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "v20251014123459",
  "uptime_seconds": 45
}
```

### 2. Search the CI360 Manual

Send a search query to retrieve relevant content:

**PowerShell:**
```powershell
$body = @{
    query = "What is CI360 and how does it work?"
    top_k = 5
    include_examples = $false
    min_confidence = 0.0
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8080/mcp/search_manual" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body `
    -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Curl (Git Bash/WSL):**
```bash
curl -X POST "http://localhost:8080/mcp/search_manual" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is CI360 and how does it work?",
    "top_k": 5,
    "include_examples": false,
    "min_confidence": 0.0
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8080/mcp/search_manual",
    json={
        "query": "What is CI360 and how does it work?",
        "top_k": 5,
        "include_examples": False,
        "min_confidence": 0.0
    }
)

data = response.json()
print(f"Found {len(data['chunks'])} results")
print(f"Intent: {data['metadata']['intent']}")
print(f"\nContext:\n{data['context']}")
```

### 3. Response Format

The server returns structured JSON with:

```json
{
  "context": "Assembled context for AI consumption...",
  "chunks": [
    {
      "chunk_id": "ci360-manual_p123_c0",
      "document_id": "ci360-manual",
      "page": 123,
      "text": "Content from the manual...",
      "score": 0.95,
      "source_type": "fact"
    }
  ],
  "metadata": {
    "intent": "fact",
    "index_version": "v20251014123459",
    "retrieval_time_ms": 150
  }
}
```

## 🎯 Example Queries

### General Information
```json
{"query": "What is SAS Customer Intelligence 360?", "top_k": 5}
```

### Technical Details
```json
{"query": "What are the system requirements for CI360?", "top_k": 3}
```

### How-To Questions
```json
{"query": "How do I create a marketing campaign in CI360?", "top_k": 5}
```

### Troubleshooting
```json
{"query": "How to fix CI360 performance issues?", "top_k": 5}
```

### Features
```json
{"query": "What are the data integration capabilities?", "top_k": 5}
```

## 🔧 Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | The search query text |
| `top_k` | integer | 10 | Number of results to return |
| `include_examples` | boolean | false | Include example-based content (future) |
| `min_confidence` | float | 0.0 | Minimum confidence score (0.0-1.0) |

## 📊 Advanced Usage

### Using with AI Agents

The MCP server can be integrated with AI agents that support HTTP APIs:

```python
# Example: Using with LangChain
from langchain.tools import Tool
import requests

def search_ci360(query: str) -> str:
    response = requests.post(
        "http://localhost:8080/mcp/search_manual",
        json={"query": query, "top_k": 5}
    )
    data = response.json()
    return data["context"]

ci360_tool = Tool(
    name="CI360_Manual_Search",
    func=search_ci360,
    description="Search the CI360 manual for information about features, setup, and troubleshooting"
)
```

### Batch Processing

```python
import requests

queries = [
    "What is CI360?",
    "How to create campaigns?",
    "System requirements",
    "Data integration features",
    "Security settings"
]

results = []
for query in queries:
    response = requests.post(
        "http://localhost:8080/mcp/search_manual",
        json={"query": query, "top_k": 3}
    )
    results.append(response.json())

# Process results...
for i, result in enumerate(results):
    print(f"Query {i+1}: {queries[i]}")
    print(f"Results: {len(result['chunks'])}")
    print()
```

## 🐛 Troubleshooting

### Server Not Starting

```bash
# Check Docker is running
docker version

# View detailed logs
docker compose logs server

# Restart the server
docker compose restart server
```

### Connection Refused

```bash
# Verify the container is running
docker compose ps

# Check port binding
docker port rag_server

# Test from inside container
docker exec rag_server curl http://localhost:8080/health
```

### Slow Responses

The first query after startup may be slower as models load. Subsequent queries are cached and much faster.

### Out of Memory

If you see OOM errors, increase Docker's memory limit in Docker Desktop settings (recommend 8GB+).

## 📈 Performance Tips

1. **Caching**: The server caches query results. Identical queries return instantly.
2. **Batch Queries**: Group related queries to reuse loaded models.
3. **Tune top_k**: Start with `top_k=3` for faster responses, increase if needed.
4. **Monitor Resources**: Use `docker stats rag_server` to monitor resource usage.

## 🔄 Updating the Indexes

If you re-index the PDFs:

```bash
# Stop the server
docker compose down

# Re-run indexing (outside Docker)
python test_indexer.py

# Restart the server
docker compose up -d
```

## 📝 API Documentation

Once the server is running, view the interactive API docs:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## 🎯 Integration Examples

### Claude Desktop Integration

Add to Claude's MCP configuration:

```json
{
  "mcpServers": {
    "ci360-manual": {
      "url": "http://localhost:8080",
      "endpoints": {
        "search": "/mcp/search_manual"
      }
    }
  }
}
```

### Custom Application

```javascript
// JavaScript/Node.js example
const axios = require('axios');

async function searchManual(query) {
  const response = await axios.post('http://localhost:8080/mcp/search_manual', {
    query: query,
    top_k: 5,
    include_examples: false
  });
  
  return response.data;
}

// Usage
searchManual('What is CI360?').then(data => {
  console.log(`Found ${data.chunks.length} results`);
  console.log(data.context);
});
```

## 🛠️ Maintenance

### View Container Stats
```bash
docker stats rag_server
```

### Access Container Shell
```bash
docker exec -it rag_server /bin/bash
```

### Backup Indexes
```bash
# The indexes are in ./data/indexes/
# Simply copy this directory to back up
cp -r data/indexes data/indexes.backup
```

## 📞 Support

For issues or questions:
1. Check the logs: `docker compose logs server`
2. Verify health: `curl http://localhost:8080/health`
3. Review the implementation report: `IMPLEMENTATION_REPORT.md`

---

**Server is ready!** Start querying the CI360 manual with intelligent RAG-Fusion retrieval. 🚀