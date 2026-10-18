# Продовження роботи

Поточні запуск, статуси та межі — README.md і HANDOFF.md. Робоча гілка `codex/sovereign-life-sim-530`; exact SHA перевіряти через Git. Актуальний read-only аудит замовляє `AUDIT_PROMPT.uk.md`. Попередня Phase 2 база — `08555703a19f85aacbf3497012e3c1b910d74d88`; її звіти не є перевіркою нових змін.

Спочатку прочитай AGENTS.md, README.md, HANDOFF.md, CONTEXT_MANIFEST.json та TASKS.md. Виправлення setup/KPI/MCP/docs описано у `audit/argon-followup-scope.md`. Argon — окрема гра на 4532; Sovereign — симулятор на 4530. Жоден не є Synera production чи payment integration.

`python -B scripts/verify.py` — переносиме приймання. SDK/browser/isolation перевіряти окремо за README. Новий аудит не повинен викликати платні моделі, читати secrets, публікувати, запускати оригінальні source extraction scripts або змінювати інші проєкти. Для Python бракує справжньої rootless ізоляції; для live Synera — окремих дозволених середовищ/людей/пристроїв. Ці gates лишаються BLOCKED/NOT_RUN, доки є тільки локальні fixtures.
