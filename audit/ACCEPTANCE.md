# Приймання фундаменту — task 530

Root окремо перевірила source-copy hashes, викликала підтримувані CLI/browser entrypoints і відтворила знайдені дефекти до ремонту. Докази нижче стосуються цього пакета й exact snapshots. Звіти працівників не замінюють root acceptance.

- 17/17 скопійованих оригіналів збіглися за SHA256 і до, і після копіювання; `scripts/check_local_sources.py` повторно підтвердила вихідні файли. Оригінали не редагувалися цим завданням.
- Portable suite: 65 Conductor tests; 14 game-forge math tests; 5 package/server tests; 7 JS model/event tests. Разом 91 тест, без пропусків у цій вибраній import closure. Старі повні тести інших проєктів не оголошуються виконаними.
- Негативні перевірки відкидають змінений hash, чужий path, відсутню залежність/маніфест, зовнішню дію/режим, невідомий вузол і неправильний timestamp. У temporary-copy mutation робота помилково відновлює енергію: baseline проходить, mutant падає на assertion. Оригінальний source не змінюється.
- Браузер: select Synera → work → next day дає day2/CHF975/energy95; робоча сесія не створює оплату. Реальний JSON download містить рівно ці три дії з UTC timestamp і NOT_CONNECTED. Подробиці — `browser-acceptance.json`, приклад експорту — `browser-export-example.json`.
- Geometry guard упала до `display:block` (ширина тіл 1.6px) та пройшла після (70–88px). Немає горизонтального overflow на перевіреній вузькій ширині; browser console warnings/errors порожні.
- Два окремі bounded internal-review контракти пройшли по одному свіжому targeted followup. `repair-triage.json` зберігає прийняті PKG-01/02/F01 та первинні NO_CHANGE/NEEDS_REVIEW докази. Internal Codex review не називається review іншої родини моделей.

`scripts/verify.py` обов’язково вимагає PACKAGE_MANIFEST та actual Git-base record. Після остаточного freeze і публікації потрібні readback remote SHA/visibility/files і fresh-clone прогін. Локальні процесні звіти — `local-tests.json` / `local-fresh-clone.json` (не комітяться); фінальні ідентифікатори надаються в terminal readback/повідомленні користувачу. Маніфест — integrity, не криптографічний підпис.

Залишається відкритим за межами фундаменту: completed game, accepted old Canvas/Godot renderer/assets, actual MCP/Claude/Codex transport, receiving-model access, реальні персональні значення, Synera live/device/customer gates і підтверджений дохід. Міст/вузли не активовані, native game art не переносився. Локальний DOMOVYK status дав PRESSURE; inference не запускалася. Платних provider calls не було; subscription/electricity savings невідомі.
