# Старт перевірки з обмеженого хмарного браузера

Скопіюй ВЕСЬ текст нижче в повідомлення моделі, якщо вона не може відкривати URL, яких немає буквально в запиті. Посилання на branch є змінними: спочатку звір SHA, потім закріпи перегляд на ньому. Після публікації локальний операторський prompt підставляє точний перевірений SHA в усі URL.

---

Проведи вимогливий доказовий аудит Sovereign. Мета — придатний до використання, читабельний, чесний сценарний симулятор із візуальною якістю 8–9/10; це художній орієнтир, не автоматична оцінка. Прочитай EXTERNAL_PROMPT, AUDIT_CONTEXT, AUDIT_PROMPT.uk і розбір попереднього звіту. Повідом точний SHA й реальні можливості своїх інструментів. Попередній аудитор прочитав тільки README — не повторюй цього як завершений code review.

За кожною знахідкою дай файл/рядок, відтворення, вплив і вузький ремонт; спробуй спростувати її другим проходом. Відрізняй перевірене, NOT_READ, NOT_RUN і припущення. Не вигадуй дефектів заради суворості. Звір живі Canvas/DOM елементи зі згенерованою декорацією, перевір клавіатуру, map clicks, high-DPI, 390px і desktop, нову 17-ту башту, витрати, reload, image-failure fallback. Показуй фактичні кадри, якщо можеш запустити браузер. Без shell/browser обмеж висновок SOURCE_ONLY й залиш відповідні гейти відкритими.

Прочитай буквальні URL нижче. Якщо файл недоступний — назви точний URL і помилку, не роби висновку про його реалізацію. Огляд read-only, disposable synthetic tests дозволені. Не встановлюй пакети, не викликай провайдерів, не змінюй accounts/visibility/production, не commit/push/deploy. Не використовуй сирі чати або локальні шляхи як доступний тобі контекст. Поверни findings за пріоритетом, coverage matrix, команди/результати, обмеження й один наступний крок.

https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/EXTERNAL_PROMPT.md
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/AUDIT_CONTEXT.md
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/AUDIT_PROMPT.uk.md
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/CONTEXT_MANIFEST.json
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/PACKAGE_MANIFEST.json
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/audit/returned-audit-triage.uk.md
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/audit/visual-refinement-acceptance.json
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/DESIGN.md
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/engine-isometric-ui/index.html
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/engine-isometric-ui/styles.css
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/engine-isometric-ui/emberglass.mjs
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/engine-isometric-ui/app.mjs
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/engine-isometric-ui/scenario-forms.mjs
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/scripts/serve.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/ai-architect/runtime.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/simulation-core/unified_tick.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/simulation-core/contracts.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/simulation-core/persistence.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/mcp-bridge/command-queue.mjs
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/ai-architect/ruleforge.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/ai-architect/sandbox.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/tests/emberglass.test.mjs
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/tests/test_phase2.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/tests/test_audit_followup.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/scripts/verify.py


https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/ai-architect/assetforge.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/ai-architect/providers.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/mcp-bridge/client.py
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/audit/visual/sovereign-desktop.jpg
https://raw.githubusercontent.com/AndriiEagle/sovereign-life-sim/codex/sovereign-life-sim-530/audit/visual/sovereign-mobile.jpg
