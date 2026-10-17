# SOVEREIGN LIFE RTS / CASHFLOW 2.0

Приватний фундамент симулятора життя, фінансів, енергії та AI-проєктів у Швейцарії на 2026–2028 роки. Зібрано на Sol у задачі 530, 17.10.2026. **Це перевірювана основа й синтетичне вебдемо, а не завершена гра або запущений бізнес.**

Явний виняток Андрія від 17.10.2026: тимчасовий public-показ для незалежного рев'ю, повернення в private заплановано на **18.10.2026 09:00 Europe/Zurich** через `sovereign-private`. Це не public license; фактичну видимість звіряти в GitHub. Автоматика потребує доступного локального Codex та GitHub auth. Промпт для зовнішньої моделі — [EXTERNAL_PROMPT.md](EXTERNAL_PROMPT.md).

Почни з [HANDOFF.md](HANDOFF.md), [CONTEXT_MANIFEST.json](CONTEXT_MANIFEST.json) та [SYNERA_LAUNCH_CHECKLIST.md](SYNERA_LAUNCH_CHECKLIST.md). Продовження іншою моделлю: [EXTERNAL_PROMPT.md](EXTERNAL_PROMPT.md).

Короткий текст для копіювання на Terra: [TERRA_SUMMARY.uk.md](TERRA_SUMMARY.uk.md). Крок 3 додає 10 описаних UI/runtime surfaces, 13 компонентів із межами reuse та свіжу локальну перевірку Instagram preparation; повні джерела й SHA — `audit/step3-source-evidence.json`.

```powershell
python -B scripts/serve.py
# Відкрити http://127.0.0.1:4530/
python -B scripts/verify.py
python -B scripts/scenario.py --ticks 96 --action rest --seed 42
cd simulation-core
python -B -m revenue_lab demo
```

Python 3.11+ і Node.js 20+ для всіх перевірок; вебдемо потребує лише Python та сучасний браузер. Встановлення залежностей, credentials, платні API і production-сервіси не потрібні. Сервер слухає лише localhost і не віддає seed, audit, `.git` або інші файли репозиторію. Зупинка — Ctrl+C.

| Частина | Що вже тут | Межа |
|---|---|---|
| `CONTEXT_MANIFEST.json` | 16 проєктів/напрямів, 8 візуальних кандидатів, шляхи, хеші, статуси й прогалини | Обмежений аудит названих робочих тек; не всі файли ноутбука й не raw-чати |
| `USER_DIGITAL_TWIN_SEED.json` | Явні цілі, робочі вподобання, source labels, невідомі значення | Без медичних висновків, реального балансу й вигаданих біоритмів |
| `engine-isometric-ui/` | Оригінальна інтерактивна карта + два точні Emberglass renderer/worldpack snapshots | Карта процедурна; старий renderer не активовано, game art не перенесено |
| `simulation-core/` | Точні reusable Conductor economics та game-forge life-transition imports із тестами | Ігрові сценарії не є прогнозом, персональною/медичною моделлю або обліком платежів |
| `automation-nodes/` | Каталог існуючих власників і два approve-first source templates | Вузли вимкнено; немає автопублікації, продажів чи запуску чужих скриптів |
| `mcp-bridge/` | Типізований журнал явних дій і ручний JSON-експорт | Real-time MCP/Codex/Claude transport: NOT_CONNECTED |

Джерела скопійовано побайтно, оригінали не змінювалися. `audit/source-copies.json` містить права й SHA256; `PACKAGE_MANIFEST.json` захищає цілісність пакета, але не є підписом автора. Оригінальні повідомлення, аккаунти, `.env`, приватні клієнтські фото, ігрові бінарники й персональні журнали не включено.

Поточний Synera main на момент аудиту — `4abbd06aa6faa98a69a6bcad4fec4470e11e7676`; CI metadata для нього — success. Це не приймання live JWT-циклу двох людей, Neon recovery, фізичних Android/iPhone чи Гілберта.

Новий репозиторій — окремий агрегуючий симулятор. Канонічні game-forge, Living Arcanum, Memento й Synera зберігають своїх власників. Не замінює Harness, Context Gateway, Token Monster або KI-BUS. Публічні/комерційні права на приватні source snapshots лишаються окремою перевіркою. Не робити репозиторій публічним автоматично.
