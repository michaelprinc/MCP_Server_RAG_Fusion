$body = @{
    query = "What is CI360 and how does it work?"
    top_k = 3
    include_examples = $false
    min_confidence = 0.0
} | ConvertTo-Json

Write-Host "🔍 Testing MCP Server Search..." -ForegroundColor Cyan
Write-Host "Query: What is CI360 and how does it work?" -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/mcp/search_manual" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Search completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Results:" -ForegroundColor Cyan
    Write-Host "  - Found: $($data.chunks.Count) chunks" -ForegroundColor White
    Write-Host "  - Intent: $($data.metadata.intent)" -ForegroundColor White
    Write-Host "  - Index Version: $($data.metadata.index_version)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "📄 Top Results:" -ForegroundColor Cyan
    for ($i = 0; $i -lt [Math]::Min(3, $data.chunks.Count); $i++) {
        $chunk = $data.chunks[$i]
        Write-Host "  $($i + 1). Page $($chunk.page) (Score: $([Math]::Round($chunk.score, 3)))" -ForegroundColor Yellow
        $preview = $chunk.text.Substring(0, [Math]::Min(150, $chunk.text.Length))
        Write-Host "     $preview..." -ForegroundColor Gray
        Write-Host ""
    }
    
    Write-Host "📝 Generated Context (preview):" -ForegroundColor Cyan
    $contextPreview = $data.context.Substring(0, [Math]::Min(300, $data.context.Length))
    Write-Host $contextPreview"..." -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}