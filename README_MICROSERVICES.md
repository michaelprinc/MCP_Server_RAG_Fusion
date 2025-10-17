# RAG-Fusion MCP Server - Microservices Architecture

## 🎯 Architecture Overview

This project now features a **decentralized microservices architecture** designed for:
- **Better observability** - Identify issues at the service level
- **Independent scaling** - Scale components based on load
- **Improved fault isolation** - Failures don't cascade
- **Easier debugging** - Logs and metrics per service

## 🏗️ Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Client / Consumer                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ JSON-RPC 2.0
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         MCP Gateway Service (Port 8080)                      │
│  • Lightweight protocol handler                              │
│  • Request validation & routing                              │
│  • Error translation                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP REST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Retrieval Service (Port 8081)                        │
│  • RAG-Fusion pipeline                                       │
│  • FAISS + BM25 indexes                                      │
│  • Cross-encoder reranking                                   │
│  • Context synthesis                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ Shared Volumes
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Indexer Service (Port 8082)                          │
│  • PDF processing (multimodal)                               │
│  • OCR & image extraction                                    │
│  • Embedding generation                                      │
│  • Index building                                            │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- 8GB+ RAM available
- 10GB+ disk space

### Deploy All Services

**Option 1: Using PowerShell script (recommended)**
```powershell
.\deploy-microservices.ps1
```

**Option 2: Manual deployment**
```bash
# Build images
docker-compose -f docker-compose-microservices.yml build

# Start services
docker-compose -f docker-compose-microservices.yml up -d

# Check health
curl http://localhost:8080/health  # MCP Gateway
curl http://localhost:8081/health  # Retrieval Service
curl http://localhost:8082/health  # Indexer Service
```

### Verify Deployment

Run the comprehensive test suite:
```bash
python test_microservices.py
```

This tests:
- Service health checks
- Inter-service communication
- MCP protocol compliance
- Error handling
- Performance benchmarks

## 📊 Service Details

### MCP Gateway Service (Port 8080)

**Purpose**: Lightweight MCP protocol handler

**Key Features**:
- JSON-RPC 2.0 compliance
- Request proxying to retrieval service
- Automatic retries with exponential backoff
- Protocol error translation

**Endpoints**:
- `GET /health` - Service health check
- `POST /mcp` - Main MCP JSON-RPC endpoint

**Resource Usage**:
- Memory: 512MB - 1GB
- CPU: 0.5 - 1 core
- Startup: ~10 seconds

---

### Retrieval Service (Port 8081)

**Purpose**: Core RAG-Fusion engine

**Key Features**:
- Multi-strategy retrieval (FAISS + BM25)
- Reciprocal rank fusion
- Cross-encoder reranking (BAAI/bge-reranker-v2-m3)
- Intent-aware routing
- LRU query caching

**Endpoints**:
- `GET /health` - Service health with index status
- `POST /retrieve` - Main retrieval endpoint
- `GET /indexes` - List available indexes
- `POST /classify` - Query intent classification

**API Example**:
```bash
curl -X POST http://localhost:8081/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to configure authentication?",
    "top_k": 10,
    "include_context": true,
    "min_confidence": 0.3
  }'
```

**Resource Usage**:
- Memory: 3GB - 6GB (depends on index size)
- CPU: 2 - 4 cores
- Startup: ~30-45 seconds (model loading)

---

### Indexer Service (Port 8082)

**Purpose**: PDF processing and index building

**Key Features**:
- Multimodal PDF ingestion (text + images)
- Tesseract OCR integration
- Background job management
- Progress tracking
- PDF upload API

**Endpoints**:
- `GET /health` - Service health with PDF count
- `POST /index/build` - Trigger index build (async)
- `GET /index/jobs/{job_id}` - Check job status
- `GET /index/jobs` - List all jobs
- `POST /pdf/upload` - Upload PDF file
- `GET /pdf/list` - List available PDFs

**API Examples**:

**Upload PDF**:
```bash
curl -X POST http://localhost:8082/pdf/upload \
  -F "file=@document.pdf"
```

**Build Index**:
```bash
curl -X POST http://localhost:8082/index/build \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "fact",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "embedding_model": "BAAI/bge-m3"
  }'
```

**Check Job Status**:
```bash
curl http://localhost:8082/index/jobs/{job_id}
```

**Resource Usage**:
- Memory: 2GB - 4GB (during indexing)
- CPU: 2 - 4 cores
- Startup: ~45-60 seconds (model downloads)

## 🔍 Monitoring & Debugging

### View Logs

**All services**:
```bash
docker-compose -f docker-compose-microservices.yml logs -f
```

**Specific service**:
```bash
docker-compose -f docker-compose-microservices.yml logs -f retrieval-service
```

### Service Status
```bash
docker-compose -f docker-compose-microservices.yml ps
```

### Restart Service
```bash
docker-compose -f docker-compose-microservices.yml restart retrieval-service
```

### Health Checks

Each service provides detailed health information:

**MCP Gateway**:
```json
{
  "status": "healthy",
  "service": "mcp-gateway",
  "uptime_seconds": 3600,
  "retrieval_service_healthy": true
}
```

**Retrieval Service**:
```json
{
  "status": "healthy",
  "service": "retrieval-service",
  "index_version": "20250101-120000",
  "indexes_loaded": true
}
```

**Indexer Service**:
```json
{
  "status": "healthy",
  "service": "indexer-service",
  "pdf_files_count": 5
}
```

## 🐛 Troubleshooting

### Problem: MCP Gateway returns 503 errors

**Solution**:
1. Check retrieval service health: `curl http://localhost:8081/health`
2. View retrieval service logs: `docker logs rag_retrieval`
3. Wait for indexes to load (check startup logs)
4. Restart if needed: `docker-compose -f docker-compose-microservices.yml restart retrieval-service`

### Problem: Retrieval service slow to respond

**Solution**:
1. Check resource usage: `docker stats rag_retrieval`
2. Increase memory allocation in docker-compose-microservices.yml
3. Reduce CACHE_SIZE if memory constrained
4. Consider scaling horizontally

### Problem: Index build job fails

**Solution**:
1. Check job status: `curl http://localhost:8082/index/jobs/{job_id}`
2. View indexer logs: `docker logs rag_indexer`
3. Verify PDF files are valid
4. Check disk space: `docker exec rag_indexer df -h`
5. Increase memory if OOM errors

## 📈 Performance Tuning

### Memory Allocation

Edit `docker-compose-microservices.yml`:
```yaml
services:
  retrieval-service:
    deploy:
      resources:
        limits:
          memory: 8G  # Increase for large indexes
```

### Horizontal Scaling

Scale retrieval service:
```bash
docker-compose -f docker-compose-microservices.yml up --scale retrieval-service=3
```

Add load balancer (nginx) in front of retrieval service for distribution.

### Caching

Adjust LRU cache size:
```yaml
environment:
  CACHE_SIZE: 2000  # Increase for better hit rate
```

## 🔐 Security Considerations

### Network Isolation
- Services communicate via internal Docker network
- Only MCP Gateway (8080) exposed publicly
- Retrieval and Indexer services not directly accessible

### Volume Permissions
- Indexes are read-only for Retrieval Service
- Only Indexer Service can write to indexes

### Production Recommendations
1. Add API authentication (API keys, OAuth)
2. Use Docker secrets for sensitive configuration
3. Enable HTTPS with reverse proxy (nginx, Traefik)
4. Implement rate limiting
5. Add request logging and audit trails

## 📚 Documentation

- **[Microservices Architecture Guide](docs/MICROSERVICES_ARCHITECTURE.md)** - Comprehensive architecture documentation
- **[API Reference](docs/API_REFERENCE.md)** - Detailed API documentation (coming soon)
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🧪 Development

### Run Tests
```bash
# Integration tests
python test_microservices.py

# Individual service tests
python test_client.py
python test_retrieval.py
```

### Local Development

Run services individually:
```bash
# Retrieval service
cd services/retrieval-service
python app.py

# MCP Gateway
cd services/mcp-gateway
python app.py

# Indexer service
cd services/indexer-service
python app.py
```

## 🎯 Migration from Monolithic

If upgrading from the monolithic architecture:

1. **Backup existing data**:
   ```bash
   cp -r data/indexes data/indexes.backup
   ```

2. **Stop old container**:
   ```bash
   docker-compose down
   ```

3. **Start microservices**:
   ```bash
   docker-compose -f docker-compose-microservices.yml up -d
   ```

4. **Verify services**:
   ```bash
   python test_microservices.py
   ```

## 🤝 Contributing

Contributions welcome! Please:
1. Test changes with `test_microservices.py`
2. Update documentation
3. Follow service isolation principles
4. Add health checks for new endpoints

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- Built with FastAPI, sentence-transformers, FAISS
- Implements Model Context Protocol (MCP)
- Uses RAG-Fusion retrieval architecture
