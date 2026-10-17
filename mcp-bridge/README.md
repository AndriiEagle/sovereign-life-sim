# Phase 2 — current transport

`client.py` forwards authenticated local JSON-RPC to `127.0.0.1:4530/api/mcp` and reads SSE at `/api/mcp/stream`. The server and UI share one command dispatcher and durable journal. A fresh observed command/event acknowledgement sets `LIVE_LOCAL_BRIDGE`; restart invalidates that current-connection claim.

`scripts/mcp_server.py` uses the official pinned MCP SDK over stdio (initialize, tools/list, tools/call). `scripts/verify_mcp.py` exercises that SDK and the actual HTTP/SSE roundtrip without calling an LLM. Configure an MCP client explicitly; no global Codex/Claude configuration is changed. Model/provider sessions stay `NOT_CONNECTED` independently.

Tokens are read only from ignored local session files, never URLs or Git. `events.mjs` remains a compatibility helper for the earlier browser DTO; it does not own live state. Historical notes below describe that earlier slice.

---

## Historical foundation notes

# Міст: контракт готовий, підключення NOT_CONNECTED

`events.mjs` записує лише явні дії в цьому демо: вибір вузла, модельна робота, відпочинок, наступний день, скидання. Буфер у пам'яті — 200 подій; експорт JSON запускає користувач. Перезавантаження сторінки очищає стан. Немає спостереження за браузером/робочим столом, персональних даних, мережевого dispatch або виконання команд.

Приклад: `{"schema":"sovereign.interaction.v1","sequence":1,"occurred_at":"2026-10-17T18:00:00Z","mode":"SYNTHETIC","action":"select","node_id":"synera"}`.

Майбутній адаптер має належати чинному Harness/Token Monster або підтримуваному MCP-власнику. Він повинен перевіряти schema, версію, повторні sequence/session IDs, свіжість і дозволені ефекти; отримувати явну згоду на передачу; підтверджувати приймання кожної події та стан підключення. Цей DTO не є MCP-сервером і не доводить, що Codex/Claude бачать кліки. Втрату перших подій у кільцевому буфері видно через total_events. Повний журнал, persistence і real-time transport — окремі завдання з TASKS.md.
