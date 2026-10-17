import test from 'node:test';
import assert from 'node:assert/strict';
import { initialState, transition } from '../simulation-core/model.mjs';
test('work consumes resource without inventing money or actual payment', () => {
  const selected = transition(initialState(), { type: 'select', node: 'synera' });
  const result = transition(selected, { type: 'work' });
  assert.equal(result.cash_cents, selected.cash_cents);
  assert.equal(result.energy, 65);
  assert.equal(result.work_sessions, 1);
  assert.equal(result.settled_cash, 'NOT_CONNECTED');
  assert.equal(selected.energy, 80);
});
test('no sales still costs money, including a negative balance', () => {
  let state = initialState();
  for (let i = 0; i < 41; i++) state = transition(state, { type: 'next_day' });
  assert.equal(state.cash_cents, -2500);
  assert.equal(state.day, 41);
});
test('exhaustion blocks work and rest does not overflow', () => {
  const state = { ...initialState(), focus: 'b2b', energy: 14 };
  assert.throws(() => transition(state, { type: 'work' }), /INSUFFICIENT_ENERGY/);
  assert.equal(transition({ ...state, energy: 95 }, { type: 'rest' }).energy, 100);
});
test('foreign actions, nodes and real-world modes are rejected', () => {
  assert.throws(() => transition(initialState(), { type: 'publish' }), /UNKNOWN_ACTION/);
  assert.throws(() => transition(initialState(), { type: 'select', node: '../../secrets' }), /UNKNOWN_NODE/);
  assert.throws(() => transition({ ...initialState(), mode: 'LIVE' }, { type: 'work' }), /INVALID_STATE/);
});
