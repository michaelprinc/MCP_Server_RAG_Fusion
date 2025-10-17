# Operations Runbook

## Daily Operations

- **Health Check**
  ```powershell
  Invoke-RestMethod -Method Get -Uri http://localhost:8080/health
  ```
- **Metrics Snapshot**
  ```powershell
  Invoke-RestMethod -Method Get -Uri http://localhost:8080/metrics
  ```
- **Tail Server Logs**
  ```powershell
  docker-compose logs --follow server
  ```

## Index Build Workflow

1. Place source PDFs in `data\pdf\`.
2. Trigger the indexer profile:
   ```powershell
   docker-compose --profile manual run --rm indexer build --rev auto
   ```
3. Validate the manifest at `data\indexes\manifest.json`.
4. Reload the server to pick up the new index set:
   ```powershell
   Invoke-RestMethod -Method Post -Uri http://localhost:8080/admin/reload
   ```

## Server Management

- **Start Server**
  ```powershell
  docker-compose up -d server
  ```
- **Stop Stack**
  ```powershell
  docker-compose down
  ```
- **Update Images**
  ```powershell
  docker-compose build indexer server
  ```

## Evaluation Pipeline

```powershell
python .\tests\eval.py --dataset .\tests\eval_dataset.jsonl --k 10
```

## Backup Strategy

```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = "backups\indexes_$timestamp.tar.gz"
docker-compose exec server tar -czf - /data/indexes | Set-Content -Path $backup -Encoding Byte
Get-ChildItem backups\indexes_*.tar.gz | Sort-Object LastWriteTime -Descending | Select-Object -Skip 7 | Remove-Item
```

## Incident Response Highlights

- **Slow Queries**: Check index size and container resources (`docker stats rag_server`).
- **Low Accuracy**: Re-run evaluation suite, adjust fusion weights, revisit chunking configs.
- **Startup Failures**: Inspect logs, confirm manifest validity, ensure model downloads completed.

Refer to `docs/TROUBLESHOOTING.md` for root cause deep dives.
