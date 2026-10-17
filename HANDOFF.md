# Передача Sovereign Life Simulator

Власник: AndriiEagle. Репозиторій: `https://github.com/AndriiEagle/sovereign-life-sim`, приватний. Робоча гілка: `codex/sovereign-life-sim-530`. `audit/git-base.json` фіксує справжній стартовий commit; точний опублікований head перевіряється через `git rev-parse HEAD` і remote readback. Не записувати self-referential commit SHA в commit, який його містить.

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

Доступ наступної моделі: авторизація Codex не доводить її GitHub-доступ. Вона має самостійно прочитати private ref, назвати точний SHA, перевірити PACKAGE_MANIFEST і виконати тести зі свіжої копії. До цього receiving-model access = UNVERIFIED. Не робити репозиторій публічним для обходу. Непереносимі source references не потрібні для роботи активного демо; вони потрібні лише для майбутніх адаптацій, які лишаються заблокованими до source/license closure.

`scripts/collect_sources.py`, `scripts/build_context.py` і `scripts/inventory.py` — host-specific maintenance/extraction commands для Sol. Вони читають явно вказані оригінальні шляхи й можуть оновити curated metadata. Receiving model їх не запускає для verification. Portable приймання — `scripts/verify.py`; optional source freshness на Sol — `scripts/check_local_sources.py`.
