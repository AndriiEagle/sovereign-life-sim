// Portable DTO seam only. No network, filesystem, background collection or executor.
const ACTIONS = new Set(['select', 'work', 'rest', 'next_day', 'reset']);
const NODES = new Set(['synera', 'instagram', 'b2b', 'engine', 'rest']);
export function createEventJournal({ capacity = 200, now = () => new Date().toISOString() } = {}) {
  if (!Number.isSafeInteger(capacity) || capacity < 1 || capacity > 1000) throw new Error('INVALID_CAPACITY');
  let sequence = 0;
  let events = [];
  return {
    record(action) {
      if (!action || !ACTIONS.has(action.type)) throw new Error('UNKNOWN_EVENT');
      if (Object.keys(action).some(key => !['type', 'node'].includes(key))) throw new Error('UNEXPECTED_FIELD');
      if ((action.type === 'select' && !NODES.has(action.node)) ||
          (action.type !== 'select' && action.node !== undefined)) throw new Error('INVALID_NODE');
      const occurredAt = now();
      if (typeof occurredAt !== 'string' ||
          !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(occurredAt) ||
          !Number.isFinite(Date.parse(occurredAt)) ||
          new Date(occurredAt).toISOString() !== (occurredAt.includes('.') ? occurredAt : occurredAt.replace('Z', '.000Z'))) {
        throw new Error('INVALID_TIMESTAMP');
      }
      const event = { schema: 'sovereign.interaction.v1', sequence: ++sequence,
        occurred_at: occurredAt, mode: 'SYNTHETIC', action: action.type,
        ...(action.node ? { node_id: action.node } : {}) };
      events.push(event);
      if (events.length > capacity) events.shift();
      return { ...event };
    },
    snapshot() { return { schema: 'sovereign.interactions.v1', connection: 'NOT_CONNECTED',
      total_events: sequence, retained_events: events.map(event => ({ ...event })) }; }
  };
}
