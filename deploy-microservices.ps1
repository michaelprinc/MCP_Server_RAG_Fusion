# Microservices Deployment - Quick Start

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RAG-Fusion Microservices Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Step 1: Build images
Write-Host ""
Write-Host "Step 1: Building Docker images..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes on first build..." -ForegroundColor Gray
docker-compose -f docker-compose-microservices.yml build

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Build successful" -ForegroundColor Green

# Step 2: Start services
Write-Host ""
Write-Host "Step 2: Starting services..." -ForegroundColor Yellow
docker-compose -f docker-compose-microservices.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start services" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Services started" -ForegroundColor Green

# Step 3: Wait for services to be healthy
Write-Host ""
Write-Host "Step 3: Waiting for services to be healthy..." -ForegroundColor Yellow
Write-Host "This may take 30-60 seconds..." -ForegroundColor Gray

$maxAttempts = 60
$attempt = 0
$allHealthy = $false

while (-not $allHealthy -and $attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 2
    $attempt++
    
    try {
        # Check indexer
        $indexerHealth = Invoke-RestMethod -Uri "http://localhost:8082/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $indexerOk = $indexerHealth.status -eq "healthy"
        
        # Check retrieval
        $retrievalHealth = Invoke-RestMethod -Uri "http://localhost:8081/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $retrievalOk = $retrievalHealth.status -eq "healthy"
        
        # Check gateway
        $gatewayHealth = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $gatewayOk = $gatewayHealth.status -in @("healthy", "degraded")
        
        if ($indexerOk -and $retrievalOk -and $gatewayOk) {
            $allHealthy = $true
        } else {
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
    } catch {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

Write-Host ""

if (-not $allHealthy) {
    Write-Host "✗ Services did not become healthy in time" -ForegroundColor Red
    Write-Host "Showing service status:" -ForegroundColor Yellow
    docker-compose -f docker-compose-microservices.yml ps
    Write-Host ""
    Write-Host "Check logs with:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose-microservices.yml logs -f" -ForegroundColor White
    exit 1
}

Write-Host "✓ All services are healthy!" -ForegroundColor Green

# Step 4: Display service status
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Service Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    $indexerHealth = Invoke-RestMethod -Uri "http://localhost:8082/health"
    Write-Host ""
    Write-Host "Indexer Service (Port 8082):" -ForegroundColor Yellow
    Write-Host "  Status: $($indexerHealth.status)" -ForegroundColor White
    Write-Host "  Uptime: $($indexerHealth.uptime_seconds)s" -ForegroundColor White
    Write-Host "  PDF Files: $($indexerHealth.pdf_files_count)" -ForegroundColor White
} catch {
    Write-Host "Indexer Service: ERROR" -ForegroundColor Red
}

try {
    $retrievalHealth = Invoke-RestMethod -Uri "http://localhost:8081/health"
    Write-Host ""
    Write-Host "Retrieval Service (Port 8081):" -ForegroundColor Yellow
    Write-Host "  Status: $($retrievalHealth.status)" -ForegroundColor White
    Write-Host "  Uptime: $($retrievalHealth.uptime_seconds)s" -ForegroundColor White
    Write-Host "  Index Version: $($retrievalHealth.index_version)" -ForegroundColor White
    Write-Host "  Indexes Loaded: $($retrievalHealth.indexes_loaded)" -ForegroundColor White
} catch {
    Write-Host "Retrieval Service: ERROR" -ForegroundColor Red
}

try {
    $gatewayHealth = Invoke-RestMethod -Uri "http://localhost:8080/health"
    Write-Host ""
    Write-Host "MCP Gateway (Port 8080):" -ForegroundColor Yellow
    Write-Host "  Status: $($gatewayHealth.status)" -ForegroundColor White
    Write-Host "  Uptime: $($gatewayHealth.uptime_seconds)s" -ForegroundColor White
    Write-Host "  Retrieval Service Healthy: $($gatewayHealth.retrieval_service_healthy)" -ForegroundColor White
} catch {
    Write-Host "MCP Gateway: ERROR" -ForegroundColor Red
}

# Step 5: Quick functionality test
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Quick Functionality Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Testing retrieval service..." -ForegroundColor Yellow

$testQuery = @{
    query = "authentication"
    top_k = 5
    include_context = $true
    min_confidence = 0.0
} | ConvertTo-Json

try {
    $testResult = Invoke-RestMethod -Uri "http://localhost:8081/retrieve" -Method Post -Body $testQuery -ContentType "application/json" -TimeoutSec 10
    
    $chunkCount = $testResult.chunks.Count
    $retrievalTime = $testResult.metadata.retrieval_time_ms
    
    Write-Host "✓ Retrieval test successful!" -ForegroundColor Green
    Write-Host "  Chunks returned: $chunkCount" -ForegroundColor White
    Write-Host "  Retrieval time: ${retrievalTime}ms" -ForegroundColor White
} catch {
    Write-Host "✗ Retrieval test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Final instructions
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Yellow
Write-Host "  MCP Gateway:      http://localhost:8080" -ForegroundColor White
Write-Host "  Retrieval API:    http://localhost:8081" -ForegroundColor White
Write-Host "  Indexer API:      http://localhost:8082" -ForegroundColor White
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  View logs:        docker-compose -f docker-compose-microservices.yml logs -f" -ForegroundColor White
Write-Host "  Stop services:    docker-compose -f docker-compose-microservices.yml down" -ForegroundColor White
Write-Host "  Restart service:  docker-compose -f docker-compose-microservices.yml restart <service-name>" -ForegroundColor White
Write-Host "  Service status:   docker-compose -f docker-compose-microservices.yml ps" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test MCP protocol with your client" -ForegroundColor White
Write-Host "  2. Upload PDFs: curl -X POST -F 'file=@document.pdf' http://localhost:8082/pdf/upload" -ForegroundColor White
Write-Host "  3. Build index:  curl -X POST http://localhost:8082/index/build -H 'Content-Type: application/json' -d '{}'" -ForegroundColor White
Write-Host "  4. Read docs:    docs/MICROSERVICES_ARCHITECTURE.md" -ForegroundColor White
Write-Host ""
