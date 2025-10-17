# Microservices Deployment Checklist

## Pre-Deployment

- [ ] Docker Desktop installed and running
- [ ] Minimum 8GB RAM available
- [ ] Minimum 10GB disk space free
- [ ] PowerShell or Bash available
- [ ] Git repository up to date

## Deployment Steps

### 1. Review Architecture
- [ ] Read `MICROSERVICES_REFACTORING_SUMMARY.md`
- [ ] Review `docs/MICROSERVICES_ARCHITECTURE.md`
- [ ] Understand service boundaries and communication

### 2. Build Services
- [ ] Run: `docker-compose -f docker-compose-microservices.yml build`
- [ ] Verify all three images built successfully:
  - [ ] `rag_indexer`
  - [ ] `rag_retrieval`
  - [ ] `rag_mcp_gateway`
- [ ] Check image sizes (should be reasonable)

### 3. Start Services
- [ ] Run: `docker-compose -f docker-compose-microservices.yml up -d`
- [ ] Verify all containers started:
  - [ ] `rag_indexer` - Running
  - [ ] `rag_retrieval` - Running
  - [ ] `rag_mcp_gateway` - Running

### 4. Wait for Services to Initialize
- [ ] Wait 60 seconds for model downloads and index loading
- [ ] Monitor logs: `docker-compose -f docker-compose-microservices.yml logs -f`
- [ ] Look for success messages:
  - [ ] `[IndexerService] ✓ Indexer Service initialized`
  - [ ] `[RetrievalService] ✓ Retrieval Service initialized successfully`
  - [ ] `[MCPGateway] ✓ Connected to Retrieval Service`

### 5. Verify Health Checks
- [ ] Indexer: `curl http://localhost:8082/health`
  - [ ] Status: "healthy"
  - [ ] PDF files count shown
- [ ] Retrieval: `curl http://localhost:8081/health`
  - [ ] Status: "healthy"
  - [ ] Index version shown
  - [ ] Indexes loaded: true
- [ ] Gateway: `curl http://localhost:8080/health`
  - [ ] Status: "healthy" or "degraded"
  - [ ] Retrieval service healthy: true

### 6. Run Integration Tests
- [ ] Install test dependencies: `pip install httpx rich`
- [ ] Run: `python test_microservices.py`
- [ ] Verify all tests pass:
  - [ ] Test 1: Health Checks - PASS
  - [ ] Test 2: Retrieval Service API - PASS
  - [ ] Test 3: MCP Protocol - PASS
  - [ ] Test 4: Error Handling - PASS
  - [ ] Test 5: Performance Benchmarks - PASS

### 7. Test MCP Protocol
- [ ] Test initialize:
  ```bash
  curl -X POST http://localhost:8080/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"initialize","params":{"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
  ```
- [ ] Verify JSON-RPC response with "result" field
- [ ] Test tools/list:
  ```bash
  curl -X POST http://localhost:8080/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}'
  ```
- [ ] Verify tools array returned
- [ ] Test tools/call:
  ```bash
  curl -X POST http://localhost:8080/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"search_manual","arguments":{"query":"test","top_k":3}},"id":3}'
  ```
- [ ] Verify results returned

### 8. Test Retrieval Service Direct
- [ ] Test retrieve endpoint:
  ```bash
  curl -X POST http://localhost:8081/retrieve \
    -H "Content-Type: application/json" \
    -d '{"query":"authentication","top_k":5,"include_context":true}'
  ```
- [ ] Verify chunks returned
- [ ] Check retrieval time < 1 second
- [ ] Verify context synthesized

### 9. Test Indexer Service (Optional)
- [ ] List PDFs: `curl http://localhost:8082/pdf/list`
- [ ] Check existing indexes
- [ ] Upload test PDF (if needed):
  ```bash
  curl -X POST http://localhost:8082/pdf/upload -F "file=@test.pdf"
  ```
- [ ] Trigger index build (if needed):
  ```bash
  curl -X POST http://localhost:8082/index/build \
    -H "Content-Type: application/json" \
    -d '{"source_type":"fact","chunk_size":512}'
  ```
- [ ] Monitor job: `curl http://localhost:8082/index/jobs/{job_id}`

### 10. Performance Validation
- [ ] Response times acceptable:
  - [ ] Health checks: < 100ms
  - [ ] Retrieval (cached): < 100ms
  - [ ] Retrieval (uncached): < 1000ms
  - [ ] MCP tool call: < 2000ms
- [ ] Memory usage reasonable:
  - [ ] Gateway: < 1GB
  - [ ] Retrieval: < 6GB
  - [ ] Indexer: < 4GB
- [ ] No error logs in any service

## Post-Deployment

### 11. Monitor Services
- [ ] Set up log monitoring
- [ ] Create alerts for health check failures
- [ ] Monitor resource usage
- [ ] Track response times

### 12. Documentation
- [ ] Share deployment guide with team
- [ ] Document any custom configuration
- [ ] Update runbooks with new architecture
- [ ] Train team on new debugging procedures

### 13. Backup Plan
- [ ] Test rollback procedure:
  ```bash
  docker-compose -f docker-compose-microservices.yml down
  docker-compose up -d  # Old monolithic
  ```
- [ ] Verify rollback works
- [ ] Document rollback steps

## Troubleshooting Checklist

### Service Won't Start
- [ ] Check Docker logs: `docker logs <container_name>`
- [ ] Verify port not already in use
- [ ] Check disk space: `docker system df`
- [ ] Verify Docker daemon running

### Service Unhealthy
- [ ] Check health endpoint directly
- [ ] Review service logs for errors
- [ ] Verify dependencies (volumes, network)
- [ ] Check resource limits

### MCP Unresponsive
- [ ] Check gateway health
- [ ] Verify retrieval service healthy
- [ ] Test retrieval service directly
- [ ] Check network connectivity between services
- [ ] Review gateway logs for timeout errors

### Performance Issues
- [ ] Check resource usage: `docker stats`
- [ ] Review slow query logs
- [ ] Check index size and quality
- [ ] Monitor cache hit rate
- [ ] Consider horizontal scaling

## Success Criteria

Deployment is successful when:

- [ ] All services report "healthy" status
- [ ] All integration tests pass
- [ ] MCP protocol fully functional
- [ ] Retrieval response times < 1s (p95)
- [ ] No errors in logs (last 5 minutes)
- [ ] Resource usage within limits
- [ ] Can identify which service has issues (if any)

## Sign-off

- **Deployed by**: _________________
- **Date**: _________________
- **Environment**: [ ] Development [ ] Staging [ ] Production
- **All tests passed**: [ ] Yes [ ] No
- **Ready for use**: [ ] Yes [ ] No

---

## Quick Commands Reference

**View all logs**:
```bash
docker-compose -f docker-compose-microservices.yml logs -f
```

**View specific service**:
```bash
docker logs rag_retrieval -f
```

**Restart service**:
```bash
docker-compose -f docker-compose-microservices.yml restart retrieval-service
```

**Stop all services**:
```bash
docker-compose -f docker-compose-microservices.yml down
```

**Check service status**:
```bash
docker-compose -f docker-compose-microservices.yml ps
```

**Resource usage**:
```bash
docker stats
```

---

## Notes

- First deployment may take 10-15 minutes (model downloads)
- Subsequent startups should be 1-2 minutes
- Indexes must exist before retrieval service works
- Gateway will show "degraded" if retrieval not ready
