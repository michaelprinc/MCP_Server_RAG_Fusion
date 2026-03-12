---
mode: agent
description: "Použij tuto dovednost při práci s Oracle databází přes SQLcl MCP Server. Zahrnuje limit 5 minut, run-sql-async workflow a zrušení dotazu."
---

# SQLcl MCP Server – Skill

## Časový limit a workflow

Maximální doba čekání na jeden tool call je **5 minut (300 s)**.

Pro každý SQL dotaz:

1. Pokud dotaz může trvat >10 s nebo vrátit >500 řádků → použij `run-sql-async`
2. Po `submit` kontroluj `status` každých 30 sekund
3. Pokud `status` není `COMPLETED` po 300 s → zavolej `cancel`, informuj uživatele

Pokud uživatel napíše "zruš" / "cancel" / "stop":
→ `run-sql-async` (cancel) → `disconnect` → potvrď zrušení

## Bezpečnostní limity

| Operace | Pravidlo |
|---------|----------|
| `SELECT` bez `WHERE` | Přidej `FETCH FIRST 200 ROWS ONLY` |
| `SELECT *` | Nahraď explicitními sloupci |
| `list-connections` | Informuj o možném zpoždění |
| DML | Vyžaduj potvrzení uživatele |
| DDL `DROP/TRUNCATE` | Vyžaduj dvojité potvrzení |

## Životní cyklus spojení

- Po dokončení sady operací vždy zavolej `disconnect`
- Neudržuj spojení přes více konverzací
