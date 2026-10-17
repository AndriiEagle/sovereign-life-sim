import { initialState, transition } from '/simulation-core/model.mjs';
import { createEventJournal } from '/mcp-bridge/events.mjs';
const details = {
  synera: ['Synera', 'Підготувати чесний показ Гілберту. Код і CI знайдені; live API, фізичні пристрої й прийняття клієнтом потребують окремої перевірки.', 'КОД Є · LIVE HOLD'],
  instagram: ['Студія контенту', 'Brand Social OS і Creator Income OS мають сценарії та шаблони. Публікація потребує схвалення; дохід не підтверджений.', 'ДЖЕРЕЛА Є · ДОХІД НЕВІДОМИЙ'],
  b2b: ['Комерційний вузол', 'Conductor Revenue Lab дає локальну економіку й гіпотези послуг. Fiverr-з’єднання та оплати не підтверджені.', 'СЦЕНАРІЇ · БЕЗ ОПЛАТ'],
  engine: ['Майстерня рушія', 'Arcanum, Emberglass і Memento внесені до каталогу. Ця карта — оригінальний вебпрототип; вихідні проєкти збережені.', 'ФУНДАМЕНТ · ПРОТОТИП'],
  rest: ['Пауза', 'Умовний ресурс моделі можна відновити. Це ігрове припущення; твій реальний стан і біоритми тут не вимірюються.', 'СИНТЕТИЧНА ЕНЕРГІЯ']
};
let state = initialState();
const journal = createEventJournal();
const $ = id => document.getElementById(id);
const labels = { select: 'Обрано вузол', work: 'Робоча сесія змодельована · оплати немає', rest: 'Відпочинок змодельовано', next_day: 'Новий день · модельні витрати CHF 25', reset: 'Сценарій скинуто' };
function render() {
  $('day').textContent = `ДЕНЬ ${String(state.day + 1).padStart(2, '0')}`;
  $('cash').textContent = `CHF ${(state.cash_cents / 100).toLocaleString('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  $('energy').textContent = `${state.energy} / 100`;
  $('energy-bar').style.width = `${state.energy}%`;
  const info = state.focus && details[state.focus];
  $('focus-name').textContent = info?.[0] ?? 'Обери точку на карті';
  $('focus-description').textContent = info?.[1] ?? 'Карта показує можливі напрями. Статус коду, запущена послуга й оплата — окремі факти.';
  $('focus-status').textContent = info?.[2] ?? 'ОЧІКУЄ ВИБОРУ';
  $('work').disabled = !state.focus || state.focus === 'rest' || state.energy < 15;
  document.querySelectorAll('[data-node]').forEach(node => {
    const selected = node.dataset.node === state.focus;
    node.classList.toggle('selected', selected);
    node.setAttribute('aria-pressed', String(selected));
  });
}
function act(action) {
  state = action.type === 'reset' ? initialState() : transition(state, action);
  journal.record(action);
  const item = document.createElement('li');
  item.textContent = `${labels[action.type]}${action.node ? ': ' + details[action.node][0] : ''}`;
  $('events').prepend(item);
  while ($('events').children.length > 5) $('events').lastElementChild.remove();
  render();
}
document.querySelectorAll('[data-node]').forEach(node => node.addEventListener('click', () => act({ type: 'select', node: node.dataset.node })));
for (const [id, type] of [['work', 'work'], ['rest', 'rest'], ['next-day', 'next_day'], ['reset', 'reset']]) $(id).addEventListener('click', () => act({ type }));
$('export').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(journal.snapshot(), null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = 'sovereign-synthetic-events.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
render();
