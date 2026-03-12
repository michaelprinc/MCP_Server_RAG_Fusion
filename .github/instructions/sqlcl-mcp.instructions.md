---
applyTo: "**/*.sql,**/*.sqlnb"
---

# SQLcl MCP Server – Skill

## Pravidla pro volání nástrojů

### Výchozí chování

- **Nikdy** nespouštěj `run-sql` pro dotaz, který může vrátit více než 500 řádků nebo běžet déle než 10 sekund.
- **Vždy** použij `run-sql-async` pro analytické dotazy, FULL TABLE SCAN, JOINy přes velké tabulky a ladění PL/SQL.
- **Vždy** přidej `FETCH FIRST 200 ROWS ONLY` k `SELECT` bez explicitního `WHERE` na sloupcích s vysokou kardinalitou.

### Časový limit (5 minut)

- Maximální akceptovatelná doba čekání na výsledek jednoho tool callu je **5 minut (300 sekund)**.
- Při použití `run-sql-async`:
  1. `submit` – odešli dotaz
  2. `status` – kontroluj každých 30 sekund
  3. Pokud stav není `COMPLETED` po **300 sekundách** → **okamžitě** zavolej `cancel`
  4. Informuj uživatele o zrušení a navrhni optimalizaci dotazu nebo použití stránkování

### Zrušení dotazu

Pokud uživatel kdykoli napíše **"zruš", "cancel", "stop"** nebo ekvivalent:
1. Okamžitě zavolej `run-sql-async` s `command: "cancel"` a příslušným `task` ID.
2. Poté zavolej `disconnect`.
3. Potvrď zrušení uživateli.

---

## Workflow pro tool calls

```
Dotaz od uživatele
       │
       ▼
Je dotaz potenciálně náročný? (analytický, bez WHERE, JOIN, PL/SQL)
       │
   ANO │                     NE
       ▼                      ▼
run-sql-async (submit)    run-sql
       │
       ▼
status každých 30s → hotovo? → results
       │
  >300s? (5 min)
       ▼
    cancel → disconnect → informuj uživatele
```

---

## Bezpečnostní limity SQL

| Typ operace | Povinný limit |
|-------------|:-------------:|
| `SELECT` bez `WHERE` | `FETCH FIRST 200 ROWS ONLY` |
| `SELECT *` | Zakázáno – vyžaduj explicitní sloupce |
| DML (`INSERT/UPDATE/DELETE`) | Vyžaduj explicitní potvrzení uživatele |
| DDL (`DROP/TRUNCATE`) | Vyžaduj dvojité potvrzení |
| `list-connections` | Informuj o možném zpoždění před spuštěním |

---

## Připojení a odpojení

- Po dokončení sady operací **vždy** zavolej `disconnect`.
- Nikdy neudržuj otevřené spojení přes více než jednu uživatelskou konverzaci.
- Při chybě připojení neprodleně zastav provádění a informuj uživatele.
