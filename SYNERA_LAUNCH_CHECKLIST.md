# Phase 2: швидкий старт 48h MVP Check

Команди нижче звірені з canonical source `4abbd06aa6faa98a69a6bcad4fec4470e11e7676` ([handoff](https://github.com/AndriiEagle/synera_-MVPplus-/blob/4abbd06aa6faa98a69a6bcad4fec4470e11e7676/docs/REVIEW_HANDOFF.uk.md)). Ця фаза їх не виконувала проти live Synera. Перші 24 години — показ; до 48 годин — закриття погоджених live gates або точний BLOCKED.

```powershell
# Окрема нова копія. Node 22; без ключів для preview.
git clone --branch main https://github.com/AndriiEagle/synera_-MVPplus-.git .runtime/synera-review
git -C .runtime/synera-review switch --detach 4abbd06aa6faa98a69a6bcad4fec4470e11e7676
Set-Location .runtime/synera-review
node --test web_launch/*.test.mjs web_launch/iceberg/*.test.mjs neon/*.test.mjs plan/v6/workflow/approval-boundary.test.mjs
node web_launch/server.mjs
# Відкрити надрукований loopback URL. Це preview, не live JWT.
```

**JWT двох людей — NOT_RUN.** Для справжнього проходу потрібні погоджений rollout URL, увімкнені live readiness flags і дві окремі авторизовані browser-сесії з реальними signed JWT. Перевірена сторінка — `/real-journey.html`. У двох різних профілях пройти profile → terms → дві згоди → invitation → receiver acceptance; окремо withdrawal і заборону sender self-accept. Не вставляти JWT в команди, Git чи звіт. Preview та fixture-прохід цього не доводять.

**SQL-передумова — лише одноразовий loopback PostgreSQL:**

```powershell
# Порт уже підготовленого одноразового сервера, НЕ production.
$env:SYNERA_ACCEPTANCE_PGPORT = '55432'
node tools/meeting-status-guard-sql-acceptance.mjs --receipt=sql-local-receipt.json
Remove-Item Env:SYNERA_ACCEPTANCE_PGPORT
```

Це точний runner із canonical source: він використовує identity shim, створює й видаляє лише власні тестові бази. **Це не Neon recovery і не signed-JWT acceptance.** У перевірених джерелах немає підтвердженої універсальної команди Neon restore. Recovery залишається BLOCKED до доступу до погодженої ізольованої копії, backup/branch identifier і процедури власника; production restore не запускати. Потрібен фактичний receipt відновлення та readback даних.

---

# Synera → показ Гілберту протягом 24 годин

Мета цих 24 годин — підготувати чесний, зрозумілий показ і конкретне рішення Гілберта. Production-пілот потребує окремих live/device gates. Нижче — робота, яку ще треба виконати; ця задача не надсилала Гілберту повідомлень і не запускала Synera.

1. **0–2 год: зафіксувати зріз демо й відкрити preview.** На момент аудиту canonical `AndriiEagle/synera_-MVPplus-` main = `4abbd06aa6faa98a69a6bcad4fec4470e11e7676`; [CI 39053215224](https://github.com/AndriiEagle/synera_-MVPplus-/actions/runs/39053215224) має success для цього SHA. У чистій окремій копії перевірити SHA й виконати підтверджену README-команду `node web_launch/server.mjs` (Node 22+). Зафіксувати URL і скриншот. Написати: «Локальний preview із синтетичними сценаріями; live-пілот ще не прийнято». Зберегти Current за замовчуванням та Atelier/Night Map лише за вибором.
2. **2–5 год: пройти один показовий сценарій і одну відмову.** Потреба → взаємна відповідність → двостороння згода → запит на знайомство. Показати відкликання згоди/заблокований результат і збереження чернетки. Лише синтетичні профілі. Приймання: сценарій працює на exact SHA, видно межу fixture/local-preview; гілка на GitHub не названа деплоєм.
3. **5–8 год: зібрати матеріал для відправлення.** Один актуальний screenshot або короткий показ, три речення про конкретну користь і одне питання для Гілберта: для якої аудиторії та повторюваної проблеми він погоджується перевірити це наступним. Посилання має бути доступне й перевірене для одержувача. Саме зовнішнє повідомлення потребує прямого доручення Андрія; наявність цього checklist його не надсилає. Ціна, партнерство, попит і оплата залишаються гіпотезами до прямого підтвердження.
4. **8–18 год, лише перед реальними запрошеннями: закрити live gate.** На exact rollout: дві авторизовані особи проходять справжній signed-JWT шлях profile → mutually approved terms → invitation → receiver acceptance; окремо звіряються застосовані Neon migrations, backup/recovery та дозволений rollout. Потрібні фактичні readback/receipts; локальні fixture-тести та CI цього не замінюють. Якщо gate не закритий — показ лишається preview, реєстрацію й live-запрошення не обіцяти.
5. **До 24 год: записати рішення й одну наступну дію.** Приймання Гілберта — його явний yes/no і домовлений наступний крок, а не факт відправлення. Перед назвою «мобільний пілот» потрібні окремі фізичні Android та iPhone/Safari проходи install/update/resume/keyboard/draft preservation. Якщо пристроїв чи рішення немає — вказати точний HOLD, зберегти придатний для показу preview й домовитися про перевірку.

Історичні 668 Node PASS / 1 SKIP та 39 browser PASS стосуються перевіреного раніше зрізу. Джерела/уточнення: `audit/synera-sources.json` + `audit/synera-sources-review.json`; новіший review має пріоритет. Відсоток готовності не виведено з несумісних local/live/customer gates.
