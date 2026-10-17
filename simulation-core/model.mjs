// Original synthetic planning sandbox. No real accounts, income or health model.
const NODES = new Set(['synera', 'instagram', 'b2b', 'engine', 'rest']);
export function initialState() {
  return { mode: 'SYNTHETIC', day: 0, cash_cents: 100000, energy: 80,
    focus: null, work_sessions: 0, settled_cash: 'NOT_CONNECTED' };
}
export function transition(state, action) {
  if (state?.mode !== 'SYNTHETIC' || !Number.isSafeInteger(state.day) || state.day < 0 ||
      !Number.isSafeInteger(state.cash_cents) || !Number.isFinite(state.energy) ||
      state.energy < 0 || state.energy > 100 || !Number.isSafeInteger(state.work_sessions) ||
      state.work_sessions < 0 || state.settled_cash !== 'NOT_CONNECTED' ||
      !(state.focus === null || NODES.has(state.focus))) throw new Error('INVALID_STATE');
  if (!action || typeof action !== 'object') throw new Error('INVALID_ACTION');
  if (action.type === 'select') {
    if (!NODES.has(action.node)) throw new Error('UNKNOWN_NODE');
    return { ...state, focus: action.node };
  }
  if (action.type === 'work') {
    if (!state.focus || state.focus === 'rest') throw new Error('SELECT_WORK_NODE');
    if (state.energy < 15) throw new Error('INSUFFICIENT_ENERGY');
    return { ...state, energy: state.energy - 15, work_sessions: state.work_sessions + 1 };
  }
  if (action.type === 'rest') return { ...state, energy: Math.min(100, state.energy + 20) };
  if (action.type === 'next_day') return { ...state, day: state.day + 1,
    cash_cents: state.cash_cents - 2500, energy: Math.min(100, state.energy + 30) };
  throw new Error('UNKNOWN_ACTION');
}
