# Промпт передачі — що реалізовано у Sovereign Phase 2

Ти працюєш із `AndriiEagle/sovereign-life-sim`, гілка `codex/sovereign-life-sim-530`. Реалізація почалася від `ec0ac62336d305c44653268215a066ceb1101cad`; поточний SHA звір через Git. Спочатку прочитай AGENTS.md, поточний блок README.md та `audit/phase2-acceptance.json`. Історичні аудити стосуються попередніх зрізів.

**Що зроблено:**

- Єдиний `unified_tick` для серверу й CLI поверх незмінених source snapshots game-forge/Conductor. Сценарна економіка, ROI башт, добровільні Bio/Sleep/Weather, дебаф ×0.6 без накопичення, явний 48h-квест, обмежений експоненціальний індекс довіри.
- Жива Emberglass-карта з оригінальним atlas: усі 16 проєктів, стабільні ID, вибір вузла, максимум дві фокусні башти, хвилі та розблокування. Параметри доходу/витрат є припущеннями; actual revenue лишається невідомим.
- Автентифіковані loopback HTTP API/JSON-RPC, SSE, idempotency, fsync-журнал, відновлення після перезапуску та захист приватних шляхів. Один диспетчер для UI й агентів.
- Офіційний MCP SDK stdio adapter. Спостережено initialize → tools/list → команда → HTTP → SSE → ack. `LIVE_LOCAL_BRIDGE` не означає, що Claude/Codex/OpenRouter підключені як моделі; після рестарту потрібен новий roundtrip.
- RuleForge: офлайн-шаблони башти, явної CHF-витрати та клієнта-агента; валідація, dry-run, версії/SHA256, активація на межі тіку й відкат. Згенерований Python ніколи не імпортується у сервер.
- AssetForge: детерміновані SVG, кеш, SHA256, регенерація та оновлення текстури. Реалізовані вимкнені адаптери OpenAI/OpenRouter для правил та OpenAI для зображень; governor, бюджетні резерви, один worker, без автоматичних повторів.
- Додані перевірки нових контрактів, Windows MIME-виправлення для ES modules, документація та підтверджені source-команди Synera. Приватний runtime, ключі й generated artifacts виключені з Git та package freeze.

**Межі, які не можна називати завершеними:**

- Python: `BLOCKED_SANDBOX`. На цьому хості не знайдено rootless OCI runtime; реальне успішне виконання generated Python не прийнято. Не замінюй ізоляцію `exec`, AST-фільтром чи звичайним subprocess.
- Платні AI/image виклики: NOT_RUN, додаткові provider calls = 0, USD = 0.00. Ключ сам по собі не погоджує витрати.
- Live Synera JWT двох людей, Neon recovery, фізичні пристрої та рішення Гілберта: NOT_RUN/BLOCKED. Preview і SQL identity shim не закривають ці gates.
- MiroFish: локальний сценарний placeholder, не upstream-інтеграція. Теорія ігор не доводить наперед задані гарантії >95% / 100% щодо реальних людей.

**Як самостійно перевірити:**

```powershell
python -B scripts/serve.py
python -B scripts/verify.py
.runtime/bridge-venv/Scripts/python.exe -B scripts/verify_mcp.py
python -B scripts/verify_sandbox.py
```

Для SDK спочатку створи venv та встанови `requirements-bridge.txt`, як у README. У браузері `http://127.0.0.1:4530/`: виконай тік, додай башту бота через JSON AI Architect, перевір новий вузол і SVG, перезапусти сервер і звір збереження. Перевір також unsupported prompt, недоступний Python і повторну команду з тим самим request ID.

Поверни короткий звіт: exact SHA, відтворені результати, конкретні дефекти й блокери. Не називай повну Phase 2 завершеною, поки справжня Python-пісочниця не пройшла приймання. Остання пряма інструкція Андрія дозволяє push цього репозиторію навіть поки він Public; вона не дозволяє публікувати секрети чи інші проєкти.
