# Sovereign і Argon

Для незалежного хмарного аудитора: почни з [AUDIT_CONTEXT.md](AUDIT_CONTEXT.md) → [AUDIT_PROMPT.uk.md](AUDIT_PROMPT.uk.md), звір точний published SHA й [свіжий portable baseline](audit/cloud-audit-baseline.json). Runtime-база цього review package — `290cea886ed6c820a9dc3a1bcea47b7f7b17258f`; решта контексту доступна в цьому GitHub tree. 18.10.2026 Андрій прямо доручив повторний public-показ цього repo для аудиту; попередній private rollback виконано, job PAUSED, нового закриття не заплановано. Live visibility перевіряється в GitHub.

Два окремі локальні застосунки. Sovereign — сценарний симулятор проєктів, ресурсів і cashflow. Argon — завершена коротка пригодницька глава «Останній трамвай», у яку можна пограти. Усі CHF, події, енергія й прогрес вигадані; фактичні особисті показники залишаються невідомими.

```powershell
python -B scripts/serve.py        # Sovereign: http://127.0.0.1:4530/
# В іншому терміналі:
python -B scripts/serve_argon.py  # Argon: http://127.0.0.1:4532/
```

Python 3.11+; Node 20+ для повних перевірок. Обидва застосунки працюють без AI-ключів. Сервери слухають лише loopback і віддають лише дозволені файли. Зупинка — Ctrl+C.

## Sovereign: поточна реалізація

Єдиний `unified_tick` використовує незмінені snapshots game-forge і Conductor. Активний Emberglass renderer з оригінальним atlas показує 16 початкових проєктів, хвилі й максимум дві фокусні башти. Доступні робота/відпочинок, добровільні Bio/Sleep/Weather, дебаф ×0.6, 48h-квест, параметризована теорія ігор, SVG-іконки та офлайн JSON RuleForge. Один диспетчер обслуговує UI й MCP; зміни зберігаються в fsync-журналі з idempotency та відновленням.

### Башти й витрати

- В AI Architect обери JSON та приклад «Башта бота». У «Початкова вартість нової башти» задай CHF і прапорець списання. `auto_deduct_setup: true` списує `setup_cents` один раз при активації правила; dry-run грошей не змінює. Без прапорця сума лишається лише базою ROI.
- Для існуючого вузла відкрий «Економіка башти», задай надходження/витрати/старт і прапорець. Списання відбудеться при переході SHIPPED → Cashflow; для вже активної башти — при збереженні. Зміна параметрів, повтор запиту, відкат і перезапуск не повторюють та не повертають попереднє списання. Наступні додаткові витрати задаються окремо. ROI = (накопичений операційний результат − фактично списаний старт) / поточна явно задана база.
- «Витрата та сценарні наслідки» поєднує суму й опціональні абсолютні `kpi_modifiers`: загальний `revenue_multiplier` (0–5), `Bio_RAM` (0–100). JSON також приймає confidence/B2B hypothesis (0–100). Множник застосовується до надходжень усіх активних башт; витрати не множаться. CHF округлюються до цілих сантимів, щоденний результат розподіляється без втрати дробових тіків.
- Звичайне «Імпланти за 20 CHF» лише списує суму. Причинний вплив витрат на здоров’я чи продажі не вигадується. KPI — введені оператором гіпотези. При відкаті вже проведена витрата та її одноразові KPI-ефекти не переграються. Змінити гіпотезу можна новим явним правилом.

Відмова через нестачу сценарних коштів або невалідний параметр атомарна. При втраті відповіді кнопка «Повторити підтвердження» використовує той самий збережений ID; він переживає reload.

### MCP

```powershell
python -m venv .runtime/bridge-venv
.runtime/bridge-venv/Scripts/python.exe -m pip install -r requirements-bridge.txt
python -B scripts/configure_mcp.py
.runtime/bridge-venv/Scripts/python.exe -B scripts/verify_mcp.py --project-config
```

На Linux/macOS interpreter — `.runtime/bridge-venv/bin/python`. Реєстратор створює лише приватний `.codex/config.toml` цього checkout, з абсолютними шляхами поточного хоста; він виключений із Git та package freeze. Чинний конфліктний запис не перезаписується. Codex завантажує проєктний MCP у trusted project при наступному старті/перепідключенні; [офіційна документація](https://learn.chatgpt.com/docs/extend/mcp?surface=cli). Наявний чат не отримує нові tools автоматично.

Адаптер автоматично проходить реальний HTTP command → SSE → ack при старті та зміні сесії сервера. SDK-перевірка виконує initialize/list/call і перевіряє цей обмін. Після рестарту статус спочатку NOT_CONNECTED; свіжий успішний обмін знову дає LIVE_LOCAL_BRIDGE. Простий health-ping цього статусу не встановлює. Claude/Codex/provider model sessions лишаються окремо NOT_CONNECTED. Жодна модель не викликається під час цих перевірок. Деталі: [mcp-bridge/README.md](mcp-bridge/README.md).

### Збереження та межі

Канонічний журнал — `.runtime/simulator/events.jsonl`, snapshot — відновлюваний кеш. Для приватного backup зупини сервер і скопіюй усю директорію; відновлення — `python -B scripts/serve.py --state-dir <копія>`. Нова версія приймає старі journals без переписування історії; прапорець автосписання за замовчуванням false. Обрізаний незавершений хвіст зберігається окремо; зіпсований завершений запис блокує старт.

Python-правила — **BLOCKED_SANDBOX** до реального rootless OCI runtime, pinned локального образу та успіху `python -B scripts/verify_sandbox.py`. На перевіреному хості runtime відсутній. Host exec як fallback заборонений. Офлайн JSON працює без пісочниці. Платні text/image adapters вимкнені й не перевірені live; [контракти RuleForge, ізоляція та бюджетні межі](ai-architect/README.md).

Live Synera JWT двох користувачів, Neon recovery, фізичні Android/iPhone та рішення Гілберта — окремі **NOT_RUN/BLOCKED** гейти. Натискання SHIPPED або verify_milestone у сценарії їх не закриває. [Потрібні реальні докази](SYNERA_LAUNCH_CHECKLIST.md).

## Argon: гра

Чотири локації, предмети, переходи, альтернативні маршрути, три фінали, автозбереження та ручна контрольна точка. [Керування, старт і збереження](argon-game/README.md). Процедурні сцени працюють без зовнішніх файлів; опціональні локальні PNG не копіюються в пакет. Argon використовує окреме збереження `.runtime/argon` і той самий перевірений Store.

## Перевірка та передача

```powershell
python -B scripts/verify.py
python -B scripts/scenario.py --ticks 96 --action rest --seed 42
```

Пакет перевіряє 17 точних source snapshots, збереження невідомих параметрів, Python/Node-контракти й сценарій. Browser, SDK та rootless sandbox мають окремі результати. [Розбір аудиту Аргона](audit/argon-followup-scope.md), [поточне приймання](audit/argon-followup-acceptance.json), [новий промпт аудиту](AUDIT_PROMPT.uk.md), [HANDOFF](HANDOFF.md), [наступні кроки](TASKS.md).

Історичні описи Phase 1 винесено в [архів README](audit/phase1-readme-snapshot.md); попередній `audit/phase2-acceptance.json` стосується попереднього зрізу. [Manifest](CONTEXT_MANIFEST.json) містить джерела й межі; [RIGHTS](RIGHTS.md) зберігає права. Public review не надає нової public/commercial ліцензії. Видимість репозиторію перевіряється в GitHub; графік повернення private не є доказом його виконання. Поточне пряме доручення дозволяє push цієї гілки навіть поки Public; secrets/runtime/account config не публікуються.
