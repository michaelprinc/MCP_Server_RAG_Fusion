# Zpráva dostupných MCP serverů

**Datum kontroly:** 5. března 2026  
**Projekt:** `MCP_Server_RAG_Fusion`

## 1. Shrnutí

V tomto repozitáři jsou aktuálně dohledatelné **3 MCP serverové varianty**:

1. Monolitický RAG-Fusion server (`server`)
2. Mikroservisní MCP Gateway (`mcp-gateway`)
3. SQLcl MCP server (šablona konfigurace pro Cline)

Při runtime kontrole na `localhost` nejsou momentálně služby dostupné (porty timeout). Docker daemon také není dostupný.

## 2. Přehled dostupných serverů

| Server | Transport | Definice v repu | Expozice | Aktuální stav |
|---|---|---|---|---|
| RAG-Fusion Monolith (`server`) | HTTP (FastAPI) | `server/app.py`, `docker-compose.yml` | `http://localhost:8080/mcp/...` | Nedostupný (timeout) |
| RAG-Fusion MCP Gateway (`mcp-gateway`) | HTTP JSON-RPC 2.0 | `services/mcp-gateway/app.py`, `docker-compose-microservices.yml` | `POST http://localhost:8080/mcp` | Nedostupný (timeout) |
| SQLcl MCP (`sqlcl`) | stdio | `configs/sqlcl-mcp/cline_mcp_settings.template.json` | `sql.exe -mcp` (placeholder cesta) | Pouze šablona, nespouštěno |

## 3. MCP schopnosti podle variant

### 3.1 Monolitický server (`server`)

Registrované endpointy pod prefixem `/mcp`:
- `POST /mcp/search_manual`
- `POST /mcp/get_chunk_details`
- `POST /mcp/open_pdf_page`
- `GET /mcp/list_indexed_documents`

Poznámka: tato varianta používá HTTP endpointy (nikoliv JSON-RPC metodu `POST /mcp`).

### 3.2 MCP Gateway (`mcp-gateway`)

Implementované MCP metody (`POST /mcp`):
- `initialize`
- `tools/list`
- `tools/call`
- `resources/list`
- `prompts/list`

Aktuálně vracené nástroje v `tools/list`:
- `search_manual`
- `get_chunk_details`

### 3.3 SQLcl MCP (`sqlcl`)

Šablona obsahuje server:
- Název: `sqlcl`
- Typ: `stdio`
- Příkaz: `C:/PATH/TO/sqlcl/bin/sql.exe -mcp`
- Timeout: `120`

Jde o konfigurační template, ne o ověřený běžící server v tomto workspace.

## 4. Zjištěné nesoulady

1. `configs/mcp-tools.json` definuje 4 nástroje (`search_manual`, `get_chunk_details`, `open_pdf_page`, `list_indexed_documents`), ale mikroservisní `mcp-gateway` aktuálně zveřejňuje jen 2 nástroje.
2. Monolitický server je označen jako MCP server, ale interface je endpoint-oriented (`/mcp/<tool>`), zatímco gateway je JSON-RPC 2.0 (`POST /mcp`).

## 5. Kontrola dostupnosti (provedeno)

- `http://localhost:8080/health` -> timeout
- `http://localhost:8081/health` -> timeout
- `http://localhost:8082/health` -> timeout
- `docker ps` -> Docker daemon nedostupný (`dockerDesktopLinuxEngine` pipe not found)

## 6. Doporučený další krok

Pro zprovoznění MCP serveru použijte jednu variantu:

1. Monolit:
   - `docker-compose up -d`
2. Mikroservisy:
   - `docker-compose -f docker-compose-microservices.yml up -d`

Poté znovu ověřte `/health` endpointy.
