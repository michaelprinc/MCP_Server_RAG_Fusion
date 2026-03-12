# SQLcl MCP Server – Implementační report: Konfigurace timeoutu

**Datum:** 18. února 2026  
**Verze SQLcl:** 25.4.2 (součást Oracle SQL Developer Extension v25.4.1)  
**Prostředí:** VS Code s GitHub Copilot, Windows

---

## 1. Shrnutí problému

Při použití SQLcl MCP serveru v rámci VS Code může dojít k dlouhotrvajícímu "zaseknutí" při volání některých nástrojů (tools), což výrazně snižuje pracovní efektivitu. Cílem je konfigurace timeoutu pro požadavky na nástroje MCP serveru s možností přenositelnosti nastavení na jiný počítač.

---

## 2. Výsledky průzkumu

### 2.1 Dostupné nástroje SQLcl MCP serveru

SQLcl MCP server (v25.4.2) poskytuje **7 nástrojů**:

| Nástroj | Popis | Parametr timeout |
|---------|-------|:----------------:|
| `connect` | Připojení k databázi | ❌ |
| `disconnect` | Odpojení od databáze | ❌ |
| `list-connections` | Seznam připojení (varování: *"can take a long time"*) | ❌ |
| `run-sql` | Synchronní spuštění SQL | ❌ |
| `run-sql-async` | Asynchronní spuštění SQL (submit/status/results/cancel) | ❌ (ale umožňuje cancel) |
| `run-sqlcl` | Spuštění SQLcl příkazů | ❌ |
| `schema-information` | Informace o schématu | ❌ |

**Žádný z nástrojů nemá vestavěný parametr `timeout`.**

### 2.2 Konfigurace Oracle SQL Developer Extension

Rozšíření Oracle SQL Developer (v25.4.1) obsahuje **56 konfiguračních vlastností**. Po důkladné analýze souboru `package.json` rozšíření bylo zjištěno, že:

- **Žádná vlastnost není zaměřena na timeout MCP serveru**
- MCP server je automaticky registrován přes `mcpServerDefinitionProviders` s ID `sqlclMcp`
- Rozšíření je uzavřená Java aplikace se zabudovaným JDK a SQLcl

### 2.3 VS Code MCP konfigurace (`.vscode/mcp.json`)

Formát konfigurace `.vscode/mcp.json` podporuje tyto vlastnosti pro stdio servery:

```json
{
  "servers": {
    "nazev-serveru": {
      "type": "stdio",
      "command": "...",
      "args": [],
      "env": {},
      "envFile": "..."
    }
  }
}
```

**VS Code nepodporuje vlastnost `timeout` v konfiguraci MCP serveru.** Neexistuje ani nastavení VS Code typu `chat.mcp.requestTimeout` nebo `github.copilot.chat.mcp.toolCallTimeout`.

### 2.4 MCP protokol (specifikace 2025-03-26)

Specifikace MCP doporučuje implementaci timeoutů, ale ponechává ji na klientech a SDK:

> *"Implementations SHOULD establish timeouts for all sent requests, to prevent hung connections and resource exhaustion."*

Klíčové body:
- Podpora **cancellation** přes `notifications/cancelled`
- **Progress notifications** mohou resetovat časovač timeoutu
- SDK a middleware **SHOULD** umožnit konfiguraci timeoutu per-request
- Nicméně VS Code zatím tuto konfiguraci uživatelům neposkytuje

### 2.5 Oracle dokumentace

Oficiální dokumentace SQLcl MCP serveru (Oracle) **neposkytuje žádné nastavení timeoutu**. Dokumentace se zaměřuje na:
- Monitoring přes `DBTOOLS$MCP_LOG` tabulku
- Sledování sessions přes `V$SESSION`
- Bezpečnostní doporučení

---

## 3. Dostupná řešení (workaroundy)

Vzhledem k absenci nativního timeoutu na úrovni MCP serveru i VS Code klienta existuje několik alternativních přístupů:

### 3.1 Použití `run-sql-async` místo `run-sql` (Doporučeno)

Nástroj `run-sql-async` je vestavěné řešení pro dlouhotrvající dotazy. Umožňuje:

- **`submit`** – odeslání SQL ke zpracování
- **`status`** – kontrola stavu provádění
- **`results`** – získání výsledků po dokončení
- **`cancel`** – zrušení běžícího dotazu

Toto je **primární doporučený přístup**. Lze jej vynutit prostřednictvím Copilot instrukcí (viz sekce 3.4).

### 3.2 Databázový timeout (Oracle Resource Manager)

Nastavení na úrovni Oracle databáze, aplikovatelné pro všechny sessions z MCP serveru:

```sql
-- Vytvoření resource profilu s limitem CPU/elapsed time
BEGIN
  DBMS_RESOURCE_MANAGER.CREATE_SIMPLE_PLAN(
    simple_plan => 'MCP_TIMEOUT_PLAN',
    consumer_group1 => 'MCP_GROUP',
    group1_percent => 100,
    group1_switch_group => 'CANCEL_SQL',
    group1_switch_time => 60,  -- timeout v sekundách
    group1_switch_estimate => TRUE
  );
END;
/

-- Alternativa: Oracle 19c+ MAX_IDLE_TIME
ALTER SESSION SET MAX_IDLE_TIME = 5;  -- v minutách
```

### 3.3 SQLcl Startup Script (přenositelná konfigurace)

Konfigurace VS Code rozšíření umožňuje nastavit **startup script**, který se spustí při každém připojení:

**Krok 1:** Vytvořte soubor `sqlcl_startup.sql`:

```sql
-- Nastavení timeoutu pro session
-- MAX_IDLE_TIME v minutách (Oracle 19c+)
ALTER SESSION SET MAX_IDLE_TIME = 5;

-- Alternativa: Nastavení SQL*Net timeout
-- (vyžaduje oprávnění DBA)
-- ALTER SYSTEM SET SQLNET.RECV_TIMEOUT = 60;
```

**Krok 2:** Přidejte do VS Code `settings.json`:

```json
{
  "sqldeveloper.connections.startupScript.path": "${workspaceFolder}/configs/sqlcl_startup.sql"
}
```

### 3.4 Copilot instrukce (`.github/copilot-instructions.md`) – přenositelné

Přidání pravidel do instrukcí pro Copilot, které zajistí preferenci `run-sql-async` a bezpečnější chování:

```markdown
## SQLcl MCP Server – pravidla pro nástroje

### Povinná pravidla
- Pro SQL dotazy, které mohou trvat déle než 10 sekund, VŽDY použij nástroj 
  `run-sql-async` místo `run-sql`.
- Před spuštěním `run-sql` pro potenciálně náročný dotaz, přidej do SQL klauzuli 
  `FETCH FIRST 100 ROWS ONLY` jako bezpečnostní limit.
- Po použití `run-sql-async` s příkazem `submit` pravidelně kontroluj stav 
  pomocí příkazu `status`.
- Pokud dotaz běží déle než 120 sekund, použij příkaz `cancel` k jeho zrušení.

### Doporučená pravidla
- Pro operace `list-connections` a `schema-information`, které mohou trvat 
  dlouho, informuj uživatele o možném čekání.
- Vyhýbej se `SELECT *` bez `WHERE` klauzule nebo `FETCH FIRST N ROWS ONLY` 
  na velkých tabulkách.
- Přidej timeout hint pro Oracle 21c+: `SELECT /*+ MAX_EXECUTION_TIME(30000) */`
```

### 3.5 Workspace konfigurace (`.vscode/settings.json`) – přenositelná

Pro přenositelnost na jiný počítač uložte nastavení do workspace souboru:

```json
{
  "sqldeveloper.connections.startupScript.path": "${workspaceFolder}/configs/sqlcl_startup.sql",
  "sqldeveloper.connections.browsing.fetchSize": 50,
  "sqldeveloper.logging.enable": true,
  "sqldeveloper.logging.level": "INFO"
}
```

---

## 4. Přenositelnost na jiný počítač

### Soubory pro verzování (Git):

| Soubor | Účel | Přenositelný |
|--------|------|:------------:|
| `.github/copilot-instructions.md` | Instrukce pro Copilot (vynucení `run-sql-async`) | ✅ |
| `.vscode/settings.json` | Workspace nastavení (startup script, fetch size) | ✅ |
| `configs/sqlcl_startup.sql` | SQL příkazy pro nastavení session timeoutu | ✅ |
| Databázové resource profily | Server-side timeout (jednorázové nastavení na DB) | ⚠️ (vyžaduje DBA) |

### Co je potřeba na cílovém počítači:

1. **VS Code** s rozšířením **Oracle SQL Developer** (nainstaluje se automaticky SQLcl)
2. **GitHub Copilot** rozšíření
3. Klonování repozitáře s vloženými konfiguračními soubory

---

## 5. Doporučená implementace

### Prioritní kroky:

1. **Přidání Copilot instrukcí** do `.github/copilot-instructions.md` – vynucení použití `run-sql-async` pro potenciálně dlouhé dotazy
2. **Vytvoření startup scriptu** `configs/sqlcl_startup.sql` – nastavení `MAX_IDLE_TIME` na databázové úrovni
3. **Aktualizace workspace settings** – nastavení cesty ke startup scriptu a fetch size limitu
4. **Verzování konfigurace** – commit všech souborů do Gitu

### Doporučené budoucí kroky:

- **Sledovat aktualizace** Oracle SQL Developer Extension – Oracle může v budoucích verzích přidat nativní timeout parametr
- **Otevřít feature request** u Oracle pro přidání timeout parametru do MCP server nástrojů
- **Sledovat VS Code** – Microsoft může přidat `toolCallTimeout` do MCP konfigurace (issue tracking na github.com/microsoft/vscode)

---

## 6. Omezení

| Omezení | Popis |
|---------|-------|
| Žádný nativní timeout | SQLcl MCP server ani VS Code nemají konfiguraci timeoutu pro tool calls |
| Extension-managed server | MCP server je řízen rozšířením, ne uživatelem – nelze přímo ovlivnit parametry spouštění |
| Oracle Resource Manager | Vyžaduje DBA oprávnění pro nastavení resource profilů |
| `MAX_IDLE_TIME` | Dostupné od Oracle 19c, granularita v minutách (ne sekundách) |
| `run-sql-async` | Závisí na tom, zda AI agent zvolí tento nástroj – lze vynutit pouze přes instrukce |

---

## 7. Závěr

SQLcl MCP server v aktuální verzi (25.4.2) **neposkytuje přímou konfiguraci timeoutu** pro své nástroje. VS Code rovněž **nemá nastavení** pro timeout MCP tool calls. Specifikace MCP doporučuje timeouty, ale jejich implementace závisí na konkrétním klientovi a serveru.

**Nejvhodnějším řešením** je kombinace:
1. **Copilot instrukcí** pro vynucení `run-sql-async` (přenositelné přes Git)
2. **Databázového startup scriptu** pro `MAX_IDLE_TIME` (přenositelný přes workspace)
3. **Oracle Resource Manager profilů** pro hardcoded timeout na serveru (jednorázové DBA nastavení)

Tato kombinace poskytuje vícevrstvou ochranu proti dlouhotrvajícím operacím a je plně přenositelná mezi počítači prostřednictvím verzovacího systému.
