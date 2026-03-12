# Oracle SQLcl MCP in Codex GUI (Custom MCP)

Date verified: 2026-03-05

## Recommendation

Use a thin launcher wrapper (this repository's `scripts/start-sqlcl-mcp.ps1`) instead of building a new MCP proxy server.

Reason:
- SQLcl already is an MCP server (`-mcp`), so a second MCP wrapper server adds avoidable protocol risk.
- The launcher can solve Windows path/runtime differences and still keep native stdio transport.

## Option A (direct, minimal)

Use SQLcl directly when you have a stable path:
- Command to launch: `C:\path\to\sql.exe`
- Arguments: `-mcp`

## Option B (recommended for Codex GUI)

Use the launcher from this repo:
- Command to launch: `powershell.exe`
- Arguments:
  - `-NoProfile`
  - `-ExecutionPolicy`
  - `Bypass`
  - `-File`
  - `C:\Programming\MCP_Server_RAG_Fusion\MCP_Server_RAG_Fusion\scripts\start-sqlcl-mcp.ps1`
  - `-LaunchMode`
  - `auto`

`auto` mode:
- Uses embedded Java launch when SQLcl comes from Oracle SQL Developer VS Code extension.
- Uses `sql.exe -mcp` otherwise.

## Codex GUI field mapping

- Name: `Oracle SQLcl`
- Transport: `STDIO`
- Command to launch: as in Option A or B
- Arguments: each token as a separate argument line
- Environment variables (optional):
  - `SQLCL_MCP_SQL_PATH` = absolute path to `sql.exe` (forces executable path)
- Environment variable passthrough (optional): `PATH`, `USERPROFILE`
- Working directory: repository root (or any stable folder)

## Quick local test before GUI

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-sqlcl-mcp.ps1 -DryRun
```

If the resolved command/path is correct, save the same launch setup in Codex GUI.

## Notes

- SQLcl MCP transport is stdio. Do not use Streamable HTTP unless you add a dedicated stdio->http bridge service.
- If startup fails with Java `--add-opens` option errors, keep `-LaunchMode auto` or force `-LaunchMode java`.
