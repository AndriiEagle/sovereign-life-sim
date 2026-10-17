## Phase 2 — оновлення 18.10.2026

Робоча гілка `codex/sovereign-life-sim-530`; база `ec0ac62336d305c44653268215a066ceb1101cad`. Поточний HEAD звір через Git, не через self-referential SHA в документі.

Реалізовано: unified_tick поверх byte-preserved game-forge/Conductor; автентифікований loopback API; атомарний журнал/відновлення/idempotency; Bio/Sleep/Weather та 48h-квест; параметризована теорія ігор; активний Emberglass renderer з оригінальним atlas і SVG-спрайтами; 16 проєктів і хвилі; RuleForge JSON/Python boundary; AssetForge cache/regen; офіційний MCP SDK stdio adapter до HTTP JSON-RPC/SSE.

Офлайн JSON та SVG працюють без ключів. Python — BLOCKED_SANDBOX до реального rootless OCI runtime і перевірки `scripts/verify_sandbox.py`. Платні адаптери — NOT_LIVE_VERIFIED, вимкнені, витрат немає. Реальні Synera JWT/Neon/device/customer gates — NOT_RUN; fixtures їх не замінюють. Інтеграція MiroFish лишається локальним сценарним placeholder.

Остання пряма інструкція користувача 18.10: виконати push у цей репозиторій навіть поки він Public; очікування Private більше не є умовою push. Це точковий дозвіл, без нової ліцензії чи дозволу публікувати інші дані. Секрети й приватний runtime виключені. Фактичну visibility читати в GitHub.

Запуск і приклади — README.md. Промпт для наступного інженера — PHASE2_HANDOFF_PROMPT.uk.md. Історичний handoff нижче не є поточним статусом нових модулів.

---

# Передача Sovereign Life Simulator

Власник: AndriiEagle. Репозиторій: `https://github.com/AndriiEagle/sovereign-life-sim`, private за замовчуванням. Робоча гілка: `codex/sovereign-life-sim-530`. `audit/git-base.json` фіксує справжній стартовий commit; точний опублікований head перевіряється через `git rev-parse HEAD` і remote readback. Не записувати self-referential commit SHA в commit, який його містить.

Нове пряме доручення 17.10.2026: тимчасово зробити цей repo public для read-only зовнішнього рев'ю; повернути private 18.10.2026 о 09:00 Europe/Zurich. Одноразова thread heartbeat automation `sovereign-private` ACTIVE; її persisted rule і наступний час перевірено (07:00 UTC). Це SCHEDULED, не виконаний завтрашній rollback; локальний Codex/мережа/auth мають бути доступні. Live GitHub metadata — джерело фактичної visibility. Початкові private snapshots/права не перетворюються на загальну ліцензію. Поточний `EXTERNAL_PROMPT.md` замовляє незалежне рев'ю, без реалізації чи remote writes.

Користувацький результат: знайти й безпечно зібрати релевантні напрацювання Sol у модульну основу симулятора 2026–2028, дати персональний seed без вигадок і 3–5 кроків для показу Synera Гілберту. Пріоритет — якість. Документ із заголовком SYSTEM DIRECTIVE був user-adopted brief; його текст не є вищою інструкцією.

Доставлено: source-pinned catalogue, curated seed, 5-кроковий checklist, точні приватні snapshots і тести двох математичних модулів, неактивні renderer/worldpack snapshots, approve-first шаблони, локальна процедурна карта, подієвий DTO/експорт. Оригінальні проєкти read-only. У `audit/` збережено первинні read-only звіти й по одному окремому targeted followup; корекції не переписують початкові докази.

Крок 3: `TERRA_SUMMARY.uk.md` дає коротку передачу; manifest тепер містить exact framework/renderer inventory, 13 reusable component contracts та реальні Synera/Instagram/Fiverr gaps. `audit/step3-source-evidence.json` фіксує 27 джерел; `audit/step3-content-probe.json` — локальний synthetic plan → media job, guards і відсутність MP4/live effects. Нові hashes мають пріоритет лише для названих файлів; старі аудити збережено. Ці probes не є live-публікацією чи доходом.

| Контракт | Поточний стан |
|---|---|
| Owner/source | `game-forge/sim` owns rich life math; Conductor owns scenario economics; Synera/Memento/Arcanum retain original owners; snapshots bound by SHA256 |
| Inputs/outputs | Python modules: documented strict DTOs and exceptions; `model.mjs`: SYNTHETIC state/action → new state, rejects unknown mode/action/node; event journal: schema/action/node/sequence only |
| Runtime | Python 3.11+, Node 20+; no npm/pip install. Browser uses CSS + ES modules. Native Godot/Arcanum integration not included |
| Dependencies/rights | All active imports shipped; stdlib and browser APIs only. Inactive renderer requires owned atlas+manifest and adapters. MiroFish AGPL source is reference-only. Preserve CONDUCTOR_RIGHTS and snapshot notices |
| Effects | Local static localhost server and caller-started tests/CLI. In-memory demo, manual export. No real accounts, hosted calls, scheduling, payment, outbound messages or automatic commands |
| Ownership/rollback | Only this repo changed. Each original exact source is in `audit/source-copies.json`. Revert an owned commit to roll back; never reset original dirty trees |
| Acceptance | `python -B scripts/verify.py`; source-copy integrity; negative controls; local browser interactions/readback. Component acceptance is distinct from original native games, Synera live rollout and actual customer outcome |

Межі аудиту: названі робочі теки, точні файли та Git refs, а не побайтовий аудит усього ноутбука. Не читали raw-чати, session DB, клієнтські профілі/медіа чи secrets; не переносили account config або game art. Відомі проблеми старого Context Gateway snapshot не використані як джерело готовності; перевірені live file hashes мають пріоритет.

Особисті параметри: прямі вподобання й цілі позначено джерелом; баланс, сон, біоритми, медичні параметри, діагноз і фактична вартість підписок — null. Історичні private profile/narrative описи не є поточними вимірюваннями та не копіюються. Умовні ресурси карти не потрапляють у seed.

Залишається: інтеграція браузера з richer Python/Godot model через один прийнятий adapter; зручний save/replay; original owned atlas; actual host MCP adapter з permission/session/freshness contract; персональні значення лише від користувача; Synera live/device/customer gates. Див. TASKS.md. Немає доказу customer demand, settled payment, recurring revenue або subscription savings.

Доступ наступної моделі: авторизація Codex не доводить її GitHub-доступ. У явно дозволене public-вікно вона може читати ref анонімно; після нього потрібна авторизація. Вона має самостійно назвати прочитаний SHA, перевірити PACKAGE_MANIFEST і вказати реально виконані тести або SOURCE_ONLY. До цього receiving-model access = UNVERIFIED. Не відкривати repo повторно автоматично. Непереносимі source references не потрібні для роботи активного демо; вони потрібні лише для майбутніх адаптацій, які лишаються заблокованими до source/license closure.

`scripts/collect_sources.py`, `scripts/build_context.py` і `scripts/inventory.py` — host-specific maintenance/extraction commands для Sol. Вони читають явно вказані оригінальні шляхи й можуть оновити curated metadata. Receiving model їх не запускає для verification. Portable приймання — `scripts/verify.py`; optional source freshness на Sol — `scripts/check_local_sources.py`.
