# Контекст для незалежного хмарного аудиту — 18.10.2026

Цей файл дає контекст, який не повинен залишатися тільки в приватному чаті. Канонічний repo — `AndriiEagle/sovereign-life-sim` (id `1423646041`), branch — `codex/sovereign-life-sim-530`. Для огляду використовуй точний published SHA, переданий разом із промптом. [AUDIT_PROMPT.uk.md](AUDIT_PROMPT.uk.md) — повне завдання; [EXTERNAL_PROMPT.md](EXTERNAL_PROMPT.md) — точка входу.

## Мета користувача й актуальне доручення

Початковий задум — ізометричний симулятор життя, фінансів, енергії та AI-проєктів у Швейцарії, 2026–2028: використати вже створені модулі, показати проєкти як ігрові вузли й пов'язати сценарні дії з ресурсами. Outlive/Cashflow/MiroFish були референсами задуму; це не дозвіл на чужий art, імпорт MiroFish або прогноз доходів. Оригінальний файл brief містив заголовок SYSTEM DIRECTIVE; це був текст документа, а не вища інструкція. Його технічний зміст викладено тут; приватні психологічні припущення не публікуються як факти.

Користувач просить особливо вимогливе, доказове незалежне рев'ю з усім релевантним контекстом на GitHub. Мета аудитора — виявити реальні дефекти й межі придатності, а не підтвердити авторський звіт чи досягти вигаданих «150%». Для зовнішньої моделі зараз замовлено read-only аудит, без реалізації, remote writes або платних викликів. Окреме подальше пряме доручення локальному Codex дозволило перевірити повернений звіт, виправити UI й створити графіку; цей дозвіл не переноситься на аудитора. Особисті фінанси, сон, здоров'я, біоритми та фактичний дохід не відомі; unknown/null у seed зберігаються.

## Походження й пріоритет джерел

| Зріз | Що він означає |
|---|---|
| `8a245f8` / `64bf7dd` | Phase 1: каталог, exact snapshots, проста DOM/CSS synthetic карта; 93 portable тести в розширеному зрізі. Це історія, не опис сьогоднішнього runtime. |
| `ec0ac62336d305c44653268215a066ceb1101cad` | Попередній public-review пакет. Його одноразове повернення у private фактично підтверджено 18.10.2026 о 07:03:30 UTC. |
| `08555703a19f85aacbf3497012e3c1b910d74d88` | Phase 2 implementation; попередній SOURCE_ONLY аудит стосувався цього SHA. |
| `290cea886ed6c820a9dc3a1bcea47b7f7b17258f` | Поточна runtime-база цього audit handoff: виправлення аудиту, setup/KPI/retry/reconnect та окрема глава Argon. |
| `8f60a10` review commit | Контекст, строгий audit contract, baseline receipt і повторне public-відкриття; його runtime/тести успадковані з `290cea8`. |
| Подальша visual refinement | Оригінальний imagegen-острів, новий HUD, live Canvas overlays, виправлення keyboard focus, mobile centering/pan та відповідні semantic/visual перевірки. Джерела змінено; нові докази — `audit/visual-refinement-acceptance.json`, старий baseline не закриває нові зміни. |

Поточні source і тести — первинні докази. `audit/argon-followup-acceptance.json` та `audit/cloud-audit-baseline.json` — твердження/вимірювання, які треба незалежно звірити. Phase 1 архіви, `step3-*`, старі browser/CI receipts і framework/reuse catalog описують свої датовані зрізи. Один новий звіт не переносить старий PASS на змінені файли.

## Межі доступного коду

| Власник / поверхня | Джерела в цьому repo | Вхід → результат / головний oracle |
|---|---|---|
| Unified simulation | `simulation-core/unified_tick.py`, `contracts.py`, snapshots `game-forge/sim/`, `revenue_lab/` | State + явна команда/тіки → новий synthetic state; строгі типи, cents, RNG, відсутність часткового apply й повторних одноразових ефектів. |
| Durable state | `simulation-core/persistence.py` | Command + durable request ID → fsync journal/ack; повтор, restart і replay зберігають причинність та idempotency. |
| HTTP authority | `scripts/serve.py`, `ai-architect/runtime.py` | Loopback/session/origin/JSON checks → один dispatcher; state, commands, assets, JSON-RPC та SSE. Private paths і невірні requests відхиляються. |
| UI / renderer | `engine-isometric-ui/`, `mcp-bridge/command-queue.mjs` | DOM-форми й Canvas 2D Emberglass із власним SVG atlas; ті самі поля, durable IDs і результати, що й у core. Не дві незалежні економіки. |
| MCP | `mcp-bridge/client.py`, `scripts/mcp_server.py`, `verify_mcp.py` | SDK stdio → authenticated HTTP command → фактичний SSE event → ack. Fresh session/token обов'язкові; model session окрема. |
| Rule/AssetForge | `ai-architect/ruleforge.py`, `assetforge.py`, `runtime.py` | Offline JSON rules/SVG → validation/dry-run → stage → tick activation; version/rollback та помилки не переграють оплачені synthetic ефекти. |
| Generated Python / providers | `ai-architect/sandbox.py`, `providers.py`, `provider_worker.py` | Fail-closed gates для справжньої rootless ізоляції та явно дозволених bounded provider jobs. Наявність адаптера не доводить безпеку, live identity або billing receipt. |
| Argon | `argon-game/`, `scripts/serve_argon.py` | Окрема локальна пригодницька глава, предмети/маршрути/фінали, autosave/checkpoint/replay. Доказ сюжетного успіху не дорівнює показу Synera клієнту. |
| Context / claims | Manifest, seed, checklist, README/HANDOFF/TASKS, `audit/` | Відповідність джерелам, свіжість, переносимість, доступність контексту й чесні claim boundaries. |

Окремі canonical Synera, Instagram/Creator, Fiverr, Quantum_Trinity, token-monster, native Godot/ігри, локальні MCP клієнти та приватні бази **не включені повністю**. Їхні шляхи/хеші — provenance, не доступ. `repairs/` містить maintenance/test harness для деяких зовнішніх проєктів, не їх runtime. Не сертифікуй їх за цим пакетом й не запускай machine-specific installer. Відсутня зовнішня реалізація — named evidence gap, не proof, що її не існує.

## Ключові вимоги, які треба перевірити

- Setup debit opt-in, один раз на правильній фазі. Зміна ціни/версії, dry-run, retry, rollback та restart не створюють приховане повторне списання/повернення. Недостатні кошти і конфліктні pending rules атомарні.
- Expense KPI — явні абсолютні сценарні припущення. Множник змінює надходження, витрати не множаться; cents/rounding/partitioned ticks/ROI/runway узгоджені. Текст про витрату не вигадує причинний медичний або sales ефект.
- Durable queue зберігає ID до надсилання. Втрата відповіді, reload/restart, duplicate/foreign requests, fsync failure й пошкодження журналу не створюють два ефекти чи неправдивий ack.
- HTTP auth, Host/Origin, JSON/body bounds, private-file/asset checks та SSE cursor/session не обходяться. Не публікуй реальні local session tokens у звіті.
- `LIVE_LOCAL_BRIDGE` потребує свіжого command → SSE → ack. Health check, config registration, старий receipt або UI ack не замінюють цього. Claude/Codex/provider session лишається окремою межею.
- Generated Python не виконується на host як fallback. AST filter не є OS sandbox. Відсутність runtime означає BLOCKED, а не PASS ізоляції. Provider routes не мають обходити чинного owner, privacy/approval/budget/identity/receipt gates; перевіряй це критично, навіть якщо README обіцяє інакше.
- Argon має досяжні фінали й відновлення без softlock; corrupted/foreign/version-mismatched checkpoints та retries не руйнують state. Опціональні відсутні PNG не мають ламати процедурний fallback.

## Команди та доступні режими

```text
python -B scripts/verify.py --report audit/local-independent-audit.json
python -B scripts/serve.py --port 14530 --state-dir .runtime/independent-audit/sovereign
python -B scripts/serve_argon.py --port 14532 --state-dir .runtime/independent-audit/argon
```

Python 3.11+ і Node 20+ достатні для portable suite; активне source closure включене. Використовуй вільні loopback ports та disposable synthetic state. SDK і image validation мають окремі pinned requirements; без уже наявних залежностей познач відповідні checks NOT_RUN, не встановлюй нічого автоматично. Не запускай `configure_mcp.py` проти реального user config, host-specific extraction scripts або `repairs/apply_hardening.py`.

`scripts/collect_sources.py`, `build_context.py`, `inventory.py`, `check_local_sources.py` — Sol maintenance/extraction, не portable build. Зокрема ранній context builder не є гарантією відтворення всіх пізніших Phase 2 metadata; аудит має перевірити цей ризик, не перезаписуючи metadata під час огляду.

## Відомі відкриті gates і межі доказу

Python isolation — BLOCKED_SANDBOX до справжнього OCI acceptance. Paid providers/model sessions, live Synera signed-JWT flow, Neon recovery, фізичні Android/iPhone та рішення Гілберта не доведені цим пакетом. Не повторюй ці disclosed gates як нову вразливість; новим finding може бути конкретна помилка fail-closed, неправдивий claim або регресія.

Оригінальні джерела/notice і 17 copy hashes збережені. Raw chats, account config, `.env`, приватні runtime saves, generated payloads, native art/binaries та чужі фото не входять у handoff. Два старі Phase 1 screenshots не видаються за вигляд нового runtime; source assets доступні в repo, актуальну browser/visual перевірку виконай сам або познач NOT_RUN. Text-only модель не може оголосити pixel/acting/device acceptance.

## Публічний доступ

18.10.2026 Андрій повторно прямо доручив зробити цей repo public та опублікувати повний релевантний контекст і сильний audit prompt. Попередня одноразова automation `sovereign-private` вже PAUSED після виконаного повернення у private; нове автоматичне закриття не замовлене й не створене. Фактичну visibility звіряти через GitHub. Це не загальний дозвіл публікувати інші проєкти або нова public/commercial license; завантажені копії не відкликаються зміною visibility.

## Повернений звіт і актуальний візуальний зріз

Повернена зовнішня модель прочитала лише README, код NOT_READ і runtime NOT_RUN; `audit/returned-audit-triage.uk.md` відділяє перевірені факти від помилкових тверджень. Не наслідуй його непідтверджені дати, рядки чи CLI flags. Для обмеженого browser URL allowlist копіюй весь `CLOUD_AUDIT_START.uk.md` у запит. Поточний дизайн — `DESIGN.md`, реальні desktop/mobile кадри — `audit/visual/`. Зображення є декорацією; проєкти, стани, дії та збереження залишаються живими. Візуальний ремонт не запускав платних AI provider adapters і не приймав зовнішні product gates.
