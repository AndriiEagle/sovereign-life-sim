# Phase 2 — unified adapter

`unified_tick.py` is the active pure adapter over the byte-preserved game-forge and Conductor snapshots. Both the HTTP runtime and `scripts/scenario.py` use it. `game_theory_shield.py` contains explicit toy strategies; `persistence.py` owns the durable event transaction boundary. Generated plugins are never imported into this process.

History and original source contracts follow.

---

## Historical foundation notes

# Математичне ядро

`revenue_lab/` — точна копія оригінального Conductor Revenue Lab з дозволом одержувачу повторно використовувати код; умови в `CONDUCTOR_RIGHTS.md`, provenance в `audit/source-copies.json`. Python 3.10+; лише стандартна бібліотека. Збережені upstream-тести перевіряються заново в цьому пакеті.

```powershell
cd simulation-core
python -B -m revenue_lab demo
python -B -m unittest discover -s upstream-tests -v
```

Це арифметика сценаріїв: fee, резерв, змінні/постійні витрати, acquisition/delivery/support праця. Прикладні ставки є припущеннями fixture, не поточним прайсом провайдерів. Податки, AHV, виплати/benefits, FX, попит і реальні оплати не моделюються автоматично.

`model.mjs` — новий детермінований ігровий sandbox для браузера. Початкові CHF 1000, енергія 80, витрати CHF 25/хід, робота −15 і відпочинок +20 — явно синтетичні параметри, не дані про Андрія. Робота не створює дохід. Обидва компоненти незалежні: бухгалтерського з’єднання браузера з калькулятором ще немає.

MiroFish — reference-only: upstream `666ghj/MiroFish`, pinned source `b5b53acc57189a4a42e44a23e149dc655c98fe82`, local `package.json` declares AGPL-3.0. Його код/сервіси не імпортовано; агентні здібності й передбачувальна точність не перевірені. Повноцінні Cashflow/RTS rules, агентна модель та персональні параметри — у TASKS.md.
