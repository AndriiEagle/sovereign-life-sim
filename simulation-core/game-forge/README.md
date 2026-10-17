# Повторне використання чинного game-forge/sim

Перенесено незмінні `sim/core.py`, `params.json`, `MATH.md` та їхній math-test import closure з canonical private `AndriiEagle/game-forge`. SHA256 і точні шляхи — `audit/source-copies.json`. Поточний дозвіл Андрія покриває приватне копіювання його напрацювань; це не нова публічна/комерційна ліцензія.

Це готовий pure transition seam для 15-хвилинних **ігрових** кроків: гроші в рапенах, енергія, навички, звички й умовний burnout. Параметри — припущення ігрової моделі. Вони не описують здоров’я Андрія, не є діагнозом або персональною калібровкою. Історичні наукові/економічні посилання в оригіналі не перевірялися заново.

```powershell
python -B scripts/scenario.py --ticks 96 --action rest --seed 42
cd simulation-core/game-forge
python -B -m unittest discover -s sim/tests -t . -v
```

Запускати першу команду з кореня Sovereign. У цей snapshot не включено PNG/CSV trajectory artifacts, Godot exporter, game scripts або narrative/personal-context docs; їхні тести не заявлені як виконані. Браузерний sandbox поки використовує окрему спрощену модель. Один узгоджений adapter і parity-oracle мають передувати переходу вебдемо на це ядро.
