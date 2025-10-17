# Microservices Architecture Guide

## Overview

The RAG-Fusion MCP Server has been refactored into a **microservices architecture** with three independent services:

```
┌─────────────────────────────────────────────────────────────┐
│                    Client / MCP Consumer                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ JSON-RPC 2.0
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               MCP Gateway Service (Port 8080)                │
│  • Protocol translation (JSON-RPC ↔ HTTP)                    │
│  • Tool/Resource/Prompt registration                         │
│  • Request validation & error handling                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTP REST API
                      ▼
┌─────────────────────────────────────────────────────────────┐
│             Retrieval Service (Port 8081)                    │
│  • FAISS + BM25 index loading                                │
│  • Multi-strategy retrieval                                  │
│  • RAG-Fusion (Reciprocal Rank Fusion)                       │
│  • Cross-encoder reranking                                   │
│  • Context synthesis                                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Shared Volumes
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Indexer Service (Port 8082)                     │
│  • PDF ingestion (multimodal)                                │
│  • Text + image extraction                                   │
│  • OCR processing                                            │
│  • Document chunking                                         │
│  • Embedding generation                                      │
│  • Index building (FAISS + BM25)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Benefits

### **1. Separation of Concerns**
Each service has a single, well-defined responsibility:
- **MCP Gateway**: Protocol handling only
- **Retrieval Service**: Query processing and retrieval
- **Indexer Service**: Document processing and index building

### **2. Independent Scalability**
Scale services independently based on load:
```bash
# Scale retrieval service to 3 replicas
docker-compose up --scale retrieval-service=3
```

### **3. Improved Observability**
- Each service has its own health endpoint
- Independent logging with service tags
- Easy to identify which component is failing
- Service-specific metrics

### **4. Better Error Isolation**
- If MCP Gateway fails, retrieval still works
- If indexer crashes during build, retrieval unaffected
- Graceful degradation possible

### **5. Technology Flexibility**
- Swap out individual services without affecting others
- Upgrade dependencies per service
- Different programming languages possible

---

## Service Details

### **MCP Gateway Service**

**Purpose**: Lightweight MCP protocol handler that translates JSON-RPC requests to HTTP calls.

**Responsibilities**:
- Accept MCP JSON-RPC 2.0 requests
- Validate protocol compliance
- Register tools, resources, and prompts
- Proxy requests to Retrieval Service
- Handle retries and timeouts
- Format responses for MCP consumers

**Endpoints**:
- `GET /health` - Health check
- `POST /mcp` - Main MCP endpoint (JSON-RPC 2.0)

**Configuration**:
```yaml
environment:
  PORT: 8080
  RETRIEVAL_SERVICE_URL: http://retrieval-service:8081
  REQUEST_TIMEOUT: 30  # seconds
  MAX_RETRIES: 3
  LOG_LEVEL: INFO
```

**Resource Requirements**:
- Memory: 512MB - 1GB
- CPU: 0.5 - 1 core

---

### **Retrieval Service**

**Purpose**: Core RAG-Fusion engine for multi-strategy retrieval and reranking.

**Responsibilities**:
- Load and manage FAISS/BM25 indexes
- Query intent classification
- Multi-strategy retrieval (dense + sparse)
- Reciprocal rank fusion
- Cross-encoder reranking
- Context synthesis

**Endpoints**:
- `GET /health` - Health check with index status
- `POST /retrieve` - Main retrieval endpoint
- `GET /indexes` - List available indexes
- `POST /classify` - Query intent classification

**API Example**:
```bash
curl -X POST http://localhost:8081/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I configure authentication?",
    "top_k": 10,
    "include_context": true,
    "min_confidence": 0.3
  }'
```

**Configuration**:
```yaml
environment:
  PORT: 8081
  INDEX_DIR: /data/indexes
  ROUTER_MODE: classifier
  CACHE_SIZE: 1000
  TOP_K_INITIAL: 50
  RERANK_TOP_K: 10
```

**Resource Requirements**:
- Memory: 3GB - 6GB (depends on index size)
- CPU: 2 - 4 cores
- Startup time: ~30-45 seconds (index loading)

---

### **Indexer Service**

**Purpose**: PDF processing and index building service.

**Responsibilities**:
- Accept PDF uploads
- Multimodal content extraction (text + images)
- OCR processing for images
- Document chunking
- Embedding generation
- FAISS and BM25 index building
- Background job management

**Endpoints**:
- `GET /health` - Health check with PDF count
- `POST /index/build` - Trigger index build job
- `GET /index/jobs/{job_id}` - Check job status
- `GET /index/jobs` - List all jobs
- `POST /pdf/upload` - Upload PDF file
- `GET /pdf/list` - List available PDFs
- `DELETE /index/jobs/{job_id}` - Delete job

**API Examples**:

**Trigger Index Build**:
```bash
curl -X POST http://localhost:8082/index/build \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "fact",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "embedding_model": "BAAI/bge-m3",
    "ocr_languages": "eng"
  }'
```

**Check Job Status**:
```bash
curl http://localhost:8082/index/jobs/index-20250101-120000
```

**Upload PDF**:
```bash
curl -X POST http://localhost:8082/pdf/upload \
  -F "file=@manual.pdf"
```

**Configuration**:
```yaml
environment:
  PORT: 8082
  PDF_DIR: /data/pdf
  ARTIFACTS_DIR: /data/artifacts
  INDEX_OUTPUT_DIR: /data/indexes
  OCR_LANGUAGES: eng
  CHUNK_SIZE: 512
  CHUNK_OVERLAP: 50
```

**Resource Requirements**:
- Memory: 2GB - 4GB (depends on PDF size)
- CPU: 2 - 4 cores
- Startup time: ~45-60 seconds (model downloads)

---

## Deployment

### **Quick Start**

1. **Build all services**:
```bash
docker-compose -f docker-compose-microservices.yml build
```

2. **Start all services**:
```bash
docker-compose -f docker-compose-microservices.yml up -d
```

3. **Check service health**:
```bash
# MCP Gateway
curl http://localhost:8080/health

# Retrieval Service
curl http://localhost:8081/health

# Indexer Service
curl http://localhost:8082/health
```

4. **View logs**:
```bash
# All services
docker-compose -f docker-compose-microservices.yml logs -f

# Specific service
docker-compose -f docker-compose-microservices.yml logs -f retrieval-service
```

### **Service Dependencies**

Services start in the following order:
1. **Indexer Service** (independent, can build indexes)
2. **Retrieval Service** (depends on indexer health check)
3. **MCP Gateway** (depends on retrieval health check)

This ensures that:
- Indexes are available before retrieval service starts
- Retrieval service is ready before MCP gateway accepts requests

---

## Troubleshooting

### **Problem: MCP Gateway returns 503 errors**

**Diagnosis**:
```bash
# Check retrieval service health
curl http://localhost:8081/health

# Check gateway logs
docker logs rag_mcp_gateway
```

**Possible Causes**:
1. Retrieval service not ready (still loading indexes)
2. Retrieval service crashed
3. Network connectivity issues

**Solution**:
- Wait for retrieval service to become healthy
- Check retrieval service logs for errors
- Restart retrieval service if crashed

---

### **Problem: Retrieval Service fails to start**

**Diagnosis**:
```bash
# Check logs
docker logs rag_retrieval

# Check if indexes exist
docker exec rag_retrieval ls -l /data/indexes
```

**Possible Causes**:
1. No indexes found in `/data/indexes`
2. Corrupted index files
3. Out of memory

**Solution**:
- Build indexes first using indexer service
- Rebuild indexes if corrupted
- Increase memory allocation in docker-compose

---

### **Problem: Indexer Service job fails**

**Diagnosis**:
```bash
# Check job status
curl http://localhost:8082/index/jobs/JOB_ID

# Check logs
docker logs rag_indexer
```

**Possible Causes**:
1. Invalid PDF file
2. OCR dependencies missing
3. Out of disk space
4. Out of memory during embedding

**Solution**:
- Validate PDF file integrity
- Check Tesseract OCR installation
- Free up disk space
- Increase memory allocation

---

## Inter-Service Communication

### **HTTP Client Configuration**

**MCP Gateway → Retrieval Service**:
- Protocol: HTTP
- URL: `http://retrieval-service:8081`
- Timeout: 30 seconds
- Retries: 3 attempts with exponential backoff

**Error Handling**:
- Timeout errors: Retry with backoff
- 503 errors: Service unavailable, retry
- 500 errors: Internal error, return to client
- Network errors: Retry then fail

---

## Monitoring & Observability

### **Health Checks**

Each service exposes a `/health` endpoint:

**MCP Gateway**:
```json
{
  "status": "healthy",
  "service": "mcp-gateway",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "retrieval_service_healthy": true
}
```

**Retrieval Service**:
```json
{
  "status": "healthy",
  "service": "retrieval-service",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "index_version": "20250101-120000",
  "indexes_loaded": true
}
```

**Indexer Service**:
```json
{
  "status": "healthy",
  "service": "indexer-service",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "pdf_dir": "/data/pdf",
  "pdf_files_count": 5
}
```

### **Structured Logging**

All services use structured logging with service tags:
```
2025-10-15 12:00:00 - app - INFO - [MCPGateway] Starting MCP Gateway Service...
2025-10-15 12:00:05 - app - INFO - [RetrievalService] Loading indexes from: /data/indexes
2025-10-15 12:00:10 - app - INFO - [IndexerService] PDF directory: /data/pdf
```

### **Metrics (Optional)**

Enable Prometheus + Grafana by uncommenting the monitoring section in `docker-compose-microservices.yml`.

**Metrics endpoints**:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

---

## Performance Tuning

### **Memory Allocation**

Adjust memory limits in `docker-compose-microservices.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 6G  # Increase for large indexes
    reservations:
      memory: 3G
```

### **Caching**

Retrieval service uses LRU cache for queries:
```yaml
environment:
  CACHE_SIZE: 1000  # Increase for better hit rate
```

### **Parallel Processing**

Indexer service can process PDFs in parallel (configure in code):
```python
# In indexer/pipeline.py
max_workers = 4  # Adjust based on CPU cores
```

---

## Migration from Monolithic Architecture

### **Step 1: Back up existing indexes**
```bash
cp -r data/indexes data/indexes.backup
```

### **Step 2: Stop old container**
```bash
docker-compose down
```

### **Step 3: Start new microservices**
```bash
docker-compose -f docker-compose-microservices.yml up -d
```

### **Step 4: Verify services**
```bash
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
```

### **Step 5: Test MCP protocol**
```bash
# Use your MCP client to test
# Example with test_mcp.py
python test_mcp.py --url http://localhost:8080/mcp
```

---

## API Contracts

### **Retrieval Service API**

**POST /retrieve**

Request:
```json
{
  "query": "string",
  "top_k": 10,
  "intent": "optional string",
  "include_context": true,
  "min_confidence": 0.0
}
```

Response:
```json
{
  "chunks": [
    {
      "chunk_id": "string",
      "text": "string",
      "score": 0.95,
      "source": "string",
      "metadata": {}
    }
  ],
  "context": "synthesized context string",
  "metadata": {
    "intent": "factual",
    "retrieval_time_ms": 250,
    "candidates_retrieved": 50,
    "chunks_reranked": 10,
    "chunks_returned": 8,
    "index_version": "20250101-120000"
  }
}
```

### **Indexer Service API**

**POST /index/build**

Request:
```json
{
  "source_type": "fact",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "embedding_model": "BAAI/bge-m3",
  "ocr_languages": "eng"
}
```

Response:
```json
{
  "job_id": "index-20250101-120000",
  "status": "pending",
  "message": "Index build job created and queued"
}
```

**GET /index/jobs/{job_id}**

Response:
```json
{
  "job_id": "index-20250101-120000",
  "status": "completed",
  "started_at": "2025-10-15T12:00:00Z",
  "completed_at": "2025-10-15T12:15:00Z",
  "total_chunks": 5000,
  "error": null,
  "result": {
    "manifest_path": "/data/indexes/manifest.json",
    "total_chunks": 5000,
    "fact_chunks": 4500,
    "example_chunks": 500
  }
}
```

---

## Security Considerations

### **Network Isolation**
- Services communicate only through internal Docker network
- Only MCP Gateway exposes public port (8080)
- Retrieval and Indexer services are not directly accessible

### **Volume Permissions**
- Indexes are read-only for Retrieval Service
- Only Indexer Service can write to indexes

### **Environment Variables**
- Never commit sensitive values to git
- Use Docker secrets for production

---

## Next Steps

1. **Enable monitoring**: Uncomment Prometheus/Grafana in docker-compose
2. **Add authentication**: Implement API keys for indexer endpoints
3. **Scale horizontally**: Test with multiple retrieval service replicas
4. **Add caching layer**: Redis for distributed query caching
5. **Implement circuit breakers**: Improve resilience with Hystrix or similar

---

## Support

For issues or questions:
1. Check service logs: `docker logs <container_name>`
2. Review health endpoints
3. Consult TROUBLESHOOTING.md
4. Open GitHub issue with logs and configuration
