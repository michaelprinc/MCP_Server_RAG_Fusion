---
name: sqlcl-mcp-ops
description: Operate, validate, and troubleshoot Oracle SQLcl MCP servers over stdio with 2026 best practices. Use when requests mention SQLcl MCP, sql -mcp startup, tools/list or tools/call validation, connection errors, timeout tuning, or client configuration for Cline/Claude Code/Claude Desktop.
---

# SQLcl MCP Ops

Use this skill for operational work on SQLcl MCP server behavior, not for generic SQL tuning.

## Quick Workflow

1. Resolve runtime paths and launch strategy.
2. Verify MCP handshake and transport behavior.
3. Enumerate capabilities and validate critical tools.
4. Tune timeout and execution strategy by MCP client.
5. Diagnose failures with a symptom-first checklist.

## 1) Resolve Runtime Paths

Run discovery before any test:

```powershell
where.exe sql
Get-Command sql -ErrorAction SilentlyContinue
```

If SQLcl comes from VS Code Oracle extension on Windows, prefer extension-local paths:

- `...\.vscode\extensions\oracle.sql-developer-<ver>\dbtools\sqlcl\bin\sql.exe`
- `...\.vscode\extensions\oracle.sql-developer-<ver>\dbtools\jdk\bin\java.exe`

If `sql.exe -mcp` fails with `Unrecognized option: --add-opens`, treat it as launcher/runtime mismatch. Launch through the embedded Java command:

```powershell
& "<ext>\\dbtools\\jdk\\bin\\java.exe" `
  "--add-modules" "ALL-DEFAULT" `
  "--add-opens" "java.prefs/java.util.prefs=oracle.dbtools.win32" `
  "--add-opens" "jdk.security.auth/com.sun.security.auth.module=oracle.dbtools.win32" `
  "-Djava.net.useSystemProxies=true" `
  "-p" "<ext>\\dbtools\\sqlcl\\launch" `
  "-m" "oracle.dbtools.sqlcl.app" `
  "-mcp"
```

## 2) Verify MCP Handshake

Treat SQLcl MCP transport as newline-delimited JSON messages in this environment.
Do not assume `Content-Length` framing.

Send this sequence:

1. `initialize`
2. `notifications/initialized`
3. `tools/list`
4. `resources/list`
5. `prompts/list`

Accept server readiness only if all are true:

- `initialize` returns `protocolVersion` and `serverInfo`.
- `tools/list` returns at least one tool.
- Process remains alive until client closes stdin or terminates.

## 3) Validate Core Tools

Expect these SQLcl MCP tools (7):

1. `list-connections`
2. `connect`
3. `disconnect`
4. `run-sqlcl`
5. `run-sql`
6. `schema-information`
7. `run-sql-async`

Run minimum behavioral checks:

1. Call `list-connections` and confirm non-crashing result.
2. Call `connect` with a known invalid name and confirm deterministic error.
3. Call `run-sql` without connection and confirm `isError: true` guidance.
4. Call `schema-information` without connection and confirm connection-required error.

## 4) Optimize for Client Behavior (2026)

Apply timeout and execution settings by client:

1. Cline:
   - Set per-server timeout (`30-3600 s`).
   - Reuse `scripts/configure-sqlcl-cline-timeout.ps1` in this repository.
2. Claude Code:
   - Set `MCP_TOOL_TIMEOUT` (milliseconds).
3. Claude Desktop:
   - Treat local MCP timeout as fixed `300 s`; optimize query shape instead of waiting longer.

Prefer this execution strategy:

1. Use `run-sql` for deterministic SQL reads.
2. Use `run-sql-async` for long-running queries (`submit/status/results/cancel`).
3. Use `run-sqlcl` only for SQLcl command semantics that SQL cannot express directly.
4. Split large operations into idempotent chunks.

## 5) Troubleshooting Checklist

Use this order:

1. Startup failure:
   - Verify path exists.
   - Verify executable permissions.
   - Verify Java runtime version and launcher behavior.
2. Handshake failure:
   - Send only newline-delimited JSON.
   - Confirm correct `protocolVersion`.
3. Tool call timeouts:
   - Increase client timeout to safe limit.
   - Move heavy reads to `run-sql-async`.
   - Add DB-side limits and session governance.
4. Unknown tool errors:
   - Refresh with `tools/list`.
   - Use server-returned tool names exactly.
5. Connection failures:
   - Call `list-connections`.
   - Match `connection_name` exactly (case sensitive behavior may apply).

## 6) Reporting Standard

When reporting SQLcl MCP status, always include:

1. Exact date and timezone.
2. SQLcl version and source path.
3. Launch method (`sql.exe` vs embedded `java`).
4. Handshake result (`initialize`, `tools/list`, `resources/list`, `prompts/list`).
5. Working tool list and failing tool calls with error payload.
6. Applied timeout settings by client.

## Local Repository Anchors

Use these files as local anchors for this project:

1. `configs/sqlcl-mcp/cline_mcp_settings.template.json`
2. `scripts/configure-sqlcl-cline-timeout.ps1`
3. `IMPLEMENTATION_REPORT_SQLCL_TIMEOUT.md`
4. `SQLCL_MCP_TIMEOUT_REPORT.md`
