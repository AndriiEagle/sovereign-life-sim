Historical snapshot from mcp-bridge/README.md at 08555703a19f85aacbf3497012e3c1b910d74d88. Not current runtime status.

## Historical foundation notes

# Міст: контракт готовий, підключення NOT_CONNECTED

`events.mjs` записує лише явні дії в цьому демо: вибір вузла, модельна робота, відпочинок, наступний день, скидання. Буфер у пам'яті — 200 подій; експорт JSON запускає користувач. Перезавантаження сторінки очищає стан. Немає спостереження за браузером/робочим столом, персональних даних, мережевого dispatch або виконання команд.

Приклад: `{"schema":"sovereign.interaction.v1","sequence":1,"occurred_at":"2026-10-17T18:00:00Z","mode":"SYNTHETIC","action":"select","node_id":"synera"}`.

Майбутній адаптер має належати чинному Harness/Token Monster або підтримуваному MCP-власнику. Він повинен перевіряти schema, версію, повторні sequence/session IDs, свіжість і дозволені ефекти; отримувати явну згоду на передачу; підтверджувати приймання кожної події та стан підключення. Цей DTO не є MCP-сервером і не доводить, що Codex/Claude бачать кліки. Втрату перших подій у кільцевому буфері видно через total_events. Повний журнал, persistence і real-time transport — окремі завдання з TASKS.md.
