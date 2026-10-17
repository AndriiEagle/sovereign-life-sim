# Sovereign Life Simulator — передача на Terra, кроки 3/4

Repo: https://github.com/AndriiEagle/sovereign-life-sim (private за замовчуванням; прямо дозволений Андрієм public-показ 17.10.2026, повернення в private заплановано на 18.10.2026 09:00 Europe/Zurich через `sovereign-private`). Гілка: `codex/sovereign-life-sim-530`. Точний опублікований SHA та поточну visibility звірити в GitHub; self-referential SHA сюди не вписується. Зовнішній моделі передавати `EXTERNAL_PROMPT.md`; це read-only review.

**CONTEXT_MANIFEST.json:** 16 проєктів/напрямів, 10 конкретних UI/runtime surfaces, 13 компонентів із source refs, залежностями та чесним статусом вставлення. SHA256 і локатори 27 джерел — `audit/step3-source-evidence.json`.

- Поточний симулятор: HTML/CSS + ES modules, процедурна ізометрія DOM/CSS, без npm-залежностей. Готові зараз: карта/будівлі, ресурси/енергія/день, панель проєкту, кнопки, журнал і JSON-експорт. Turn counter є; прийнятого countdown/Pomodoro немає.
- game-forge: Godot/GDScript, 2D CanvasItem/AnimatedSprite2D, `gl_compatibility`. Діалог і герой потребують Godot, shader/data/assets closure; у вебдемо їх не вставлено. Чиста Python life-math уже перенесена.
- Архівний Emberglass: Canvas 2D. Точні renderer/worldpack snapshots уже в repo; projection/inverse/picking helpers мають окремі тести. Повний renderer потребує власного атласу й state adapter. Inventory/crafting — лише reference logic, готового UI інвентаря немає. Сучасний оригінальний Emberglass має Vite/dependencies.
- Memento/Gemeinde: React/Next.js/Tailwind, у Gemeinde також framer-motion; потрібен порт/повний import closure. Arcanum cards: DOM/CSS + Canvas particles. LEGO: заявлений Godot 4.7 / Forward Plus. Remotion/Three.js — окрема медіафабрика; video bar chart не є live-графіком гри. PixiJS/Phaser у перевірених entrypoints/manifests не підтверджені.
- Instagram: свіжий локальний synthetic smoke пройшов existing Brand monthly plan → Creator media job без нового field adapter; створено script/SRT/render-spec/scene-graph/Remotion-props. Approval pending/draft-only збережено, negative case відхилено, 4 Suno guard tests PASS. Реальний MP4, авторизований канал, approved post/receipt і analytics ще не прийняті.
- Fiverr: Conductor offline Decimal economics перевірена; live adapter/order/buyer acceptance/payout у перевіреному scope не підтверджені. Сценарний прибуток не є доходом.
- Synera: canonical main `4abbd06aa6faa98a69a6bcad4fec4470e11e7676`, CI `39053215224` success. Є Node/DOM preview та API source; profile/journey AI без `--local-ai` вимкнені (503 за кодом). Production JWT/Neon/device/customer acceptance лишаються HOLD. Це більше, ніж одне «підʼєднати ключ».

**USER_DIGITAL_TWIN_SEED.json:** явні цілі, якість як базовий пріоритет, поточне прохання діяти швидко/автономно, CHF/2026–2028 як scope моделі та привʼязки до трьох проєктів. Баланс, дохід, сон, енергія, медичні дані й фактичні витрати — null; synthetic defaults не стають персональними фактами.

**SYNERA_LAUNCH_CHECKLIST.md — 5 дій на 24 години:**

1. 0–2 год: pinned clean source → Node 22 preview → актуальний screenshot; Current default, Atelier opt-in.
2. 2–5 год: synthetic need → mutual fit → two-sided consent → intro; окремо withdrawal/blocked/draft.
3. 5–8 год: screenshot/короткий показ + 3 речення користі + 1 питання Гілберту; фактичне повідомлення лише за прямим дорученням.
4. 8–18 год, до live-запрошень: два справжні signed-JWT акаунти, Neon migrations/backup/recovery та approved rollout; інакше лишити preview.
5. До 24 год: явне рішення Гілберта + наступний крок; фізичні Android та iPhone/Safari — окремий gate мобільного пілоту.

На Terra: authenticated clone → checkout task branch → `python -B scripts/verify.py`. Python 3.11+, Node 20+, без install/credentials. Для карти: `python -B scripts/serve.py`, http://127.0.0.1:4530/. Host-specific extraction scripts не запускати: Sol paths можуть бути недоступні.

NEXT, 10–15 хв: перевірити private read access і package tests на Terra. Доступ іншої моделі не підтверджено доступом Codex. Реальні акаунти, гроші, native game/voice та production не прийняті; provider calls=0, USD=0.00.
