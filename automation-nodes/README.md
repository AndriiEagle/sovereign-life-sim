# Комерційні вузли

`catalog.json` описує наявних власників і їхні точки входу. Це каталог адаптерів, а не новий dispatcher, ledger чи queue. Усі вузли `enabled=false`, зовнішні ефекти заблоковані. Вебкарта не запускає цих команд.

- Instagram: Brand Social OS → approve-first drafts; Creator Income OS → медіапідготовка; copied `source-templates/` збережено без змін.
- B2B: Conductor Revenue Lab → локальні сценарії ціни/праці; Revenue Defense і Visual Voice Lab → перевірювані комерційні гіпотези.
- Fiverr: у перевірених джерелах немає підтвердженого live-adapter/order/payment workflow. Вузол містить лише offline planning contract.
- Synera: посилання на canonical repo та checklist; оригінал не скопійований і не задеплоєний.

Присутній скрипт/шаблон не доводить live API, публікацію, клієнтське прийняття або прибуток. Майбутній adapter повинен використовувати чинні Harness/Token Monster і явний дозвіл на ефекти; не переносити `.env`, accounts.json, customer data чи робочі журнали.
