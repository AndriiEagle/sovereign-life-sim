import test from 'node:test';
import assert from 'node:assert/strict';
import { createEventJournal } from '../mcp-bridge/events.mjs';
test('typed event export preserves order while exposing bounded retention', () => {
  const journal = createEventJournal({ capacity: 2, now: () => '2026-10-17T18:00:00Z' });
  journal.record({ type: 'select', node: 'synera' });
  journal.record({ type: 'work' });
  journal.record({ type: 'next_day' });
  const out = journal.snapshot();
  assert.equal(out.total_events, 3);
  assert.deepEqual(out.retained_events.map(event => event.sequence), [2, 3]);
  assert.equal(out.connection, 'NOT_CONNECTED');
  out.retained_events[0].action = 'tampered';
  assert.equal(journal.snapshot().retained_events[0].action, 'work');
});
test('no free-form payload, external action or foreign node enters events', () => {
  const journal = createEventJournal();
  assert.throws(() => journal.record({ type: 'select', node: 'synera', email: 'private' }), /UNEXPECTED_FIELD/);
  assert.throws(() => journal.record({ type: 'send_email' }), /UNKNOWN_EVENT/);
  assert.throws(() => journal.record({ type: 'select', node: 'unknown' }), /INVALID_NODE/);
  assert.equal(journal.snapshot().total_events, 0);
});
test('invalid clock output cannot corrupt event DTO or advance its sequence', () => {
  for (const value of [{ untyped: 'value' }, null, 123, 'tomorrow', '2026-02-30T18:00:00Z']) {
    const journal = createEventJournal({ now: () => value });
    assert.throws(() => journal.record({ type: 'work' }), /INVALID_TIMESTAMP/);
    assert.equal(journal.snapshot().total_events, 0);
    assert.deepEqual(journal.snapshot().retained_events, []);
  }
});
