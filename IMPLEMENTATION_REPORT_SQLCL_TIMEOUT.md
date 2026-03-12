# Implementation Report: Timeout pro SQLcl MCP Server

## 1. Cil

Zabranit dlouhemu zaseknuti pri volani SQLcl MCP nastroju tim, ze se pozadavek ukonci po definovanem case, a umoznit prenositelnou konfiguraci na jiny pocitac.

## 2. Datum a rozsah overeni

Overeno k datu **18. 2. 2026** na zaklade oficialni dokumentace Oracle SQLcl a MCP klientu.

## 3. Zjisteni (moznosti nastaveni)

1. SQLcl MCP server se podle Oracle dokumentace spousti pres `sql -mcp`; v popisu spusteni a klientske konfigurace neni uveden samostatny serverovy parametr pro timeout tool volani.  
   Zdroj: Oracle SQLcl MCP docs (Starting and Managing SQLcl MCP Server).

2. Timeout lze efektivne ridit na strane MCP klienta:
   - **Cline**: per-server `Network Timeout`, rozsah 30 s az 1 h, default 60 s.
   - **Claude Desktop**: timeout lokalnich MCP serveru je fixne 300 s (5 minut), bez uzivatelske konfigurace.
   - **Claude Code**: lze menit pres promennou prostredi `MCP_TOOL_TIMEOUT` (v milisekundach).

3. Pro provozni diagnostiku SQLcl MCP serveru je vhodne zapnout monitoring podle Oracle (`DBTOOLS$MCP_LOG`), aby bylo mozne dohledat zaseknuta nebo timeoutovana volani.

## 4. Implementace v repozitari

Pridany soubory:

1. `configs/sqlcl-mcp/cline_mcp_settings.template.json`
   - Prenositelna sablona konfigurace Cline MCP serveru `sqlcl`.
   - Obsahuje parametr `timeout` (sekundy), vychozi hodnota 120.

2. `scripts/configure-sqlcl-cline-timeout.ps1`
   - Automatizuje nastaveni/aktualizaci timeoutu v Cline konfiguraci.
   - Vytvari zalohu puvodniho JSON.
   - Parametry:
     - `-SqlclExecutable` (povinny): cesta na `sql.exe`
     - `-TimeoutSeconds` (volitelny, 30-3600, default 120)
     - `-ServerName` (default `sqlcl`)
     - `-ConfigPath` (default Cline storage cesta ve Windows)

## 5. Postup nasazeni na jinem pocitaci

1. Nainstalovat SQLcl (verze s MCP podporou, napr. 25.2+).
2. Overit lokalne prikaz:
   - `sql -mcp`
3. Spustit skript:
   ```powershell
   .\scripts\configure-sqlcl-cline-timeout.ps1 `
     -SqlclExecutable "C:\tools\sqlcl\bin\sql.exe" `
     -TimeoutSeconds 120
   ```
4. Restartovat MCP klienta (Cline / VS Code), aby nacetl novou konfiguraci.

## 6. Doporucene provozni hodnoty

1. Start: `120 s`
2. Tezke dotazy: `180-300 s`
3. Pokud i 300 s nestaci:
   - optimalizovat konkretni SQL dotaz,
   - zavest DB-side limity a monitoring (Oracle MCP logging),
   - nepouzivat neomezene navysovani timeoutu.

## 7. Limity

1. U **Claude Desktop** nelze timeout lokalniho MCP serveru uzivatelsky zvysit nad fixni limit 300 s.
2. Timeout na klientovi ukonci cekani klienta, ale serverova strana muze mezitim stale zpracovavat operaci; proto je dulezity take DB-side governance a monitoring.

## 8. Pouzite zdroje

1. Oracle SQLcl MCP docs (Starting and Managing):  
   https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.2/sqcug/starting-and-managing-sqlcl-mcp-server.html
2. Oracle SQLcl MCP docs (Monitoring):  
   https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.2/sqcug/monitoring-sqlcl-mcp-server-activity.html
3. Cline MCP Network Timeout:  
   https://docs.cline.bot/mcp-servers/mcp-server-timeouts
4. Cline MCP schema (`timeout`):  
   https://raw.githubusercontent.com/cline/cline/main/src/services/mcp/schemas.ts
5. Cline MCP shared defaults/constants:  
   https://raw.githubusercontent.com/cline/cline/main/src/shared/mcp.ts
6. Claude Desktop MCP timeout limit (300s):  
   https://support.claude.com/en/articles/11175166-troubleshooting-common-issues
7. Claude Code settings (`MCP_TOOL_TIMEOUT`):  
   https://docs.claude.com/en/docs/claude-code/settings
