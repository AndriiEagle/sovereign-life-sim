"""Authoritative, deterministic adventure using the existing durable Store."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'simulation-core'))
from contracts import canonical
from persistence import Store, atomic_write, digest

WORLD_BYTES = Path(__file__).with_name('world.json').read_bytes()
WORLD = json.loads(WORLD_BYTES)
WORLD_HASH = hashlib.sha256(WORLD_BYTES).hexdigest()
MAX_ACTIONS = 500


def initial_state():
    return {'schema':'argon.game.v1', 'world_hash':WORLD_HASH, 'revision':0, 'sim_time':1122,
        'location':WORLD['start'], 'energy':70, 'cash_cents':1200, 'items':['prototype'],
        'flags':[], 'visited':[WORLD['start']], 'ending':None, 'history':[],
        'note':WORLD['intro'], 'log':[WORLD['intro']]}


def disabled_reason(state, action_id):
    if state['ending']: return 'Пригоду завершено. Можна завантажити збереження або почати знову.'
    if len(state['history']) >= MAX_ACTIONS: return 'Досягнуто межі цієї пригоди. Збережи її або почни нову.'
    action = WORLD['actions'][action_id]
    if action.get('once') in state['flags']: return 'Уже зроблено'
    if action.get('cost', 0) > state['cash_cents']: return 'Бракує ігрових CHF'
    if action.get('requires_item') and action['requires_item'] not in state['items']: return 'Потрібно: ' + WORLD['items'][action['requires_item']]['name']
    if any(flag not in state['flags'] for flag in action.get('requires_flags', [])): return 'Спершу познайомся з Адою та виконай потрібні кроки'
    if state['energy'] < max(action.get('requires_energy', 0), -action.get('energy', 0)): return 'Бракує сил. Перепочинь біля води або в майстерні.'
    return None


def step(state, action_id, payload=None):
    payload = {} if payload is None else payload
    if not isinstance(action_id, str) or not isinstance(payload, dict): raise ValueError('INVALID_ACTION')
    allowed = {a for spot in WORLD['locations'][state['location']]['hotspots'] for a in spot['actions']}
    if action_id not in allowed: raise ValueError('ACTION_NOT_IN_LOCATION')
    reason = disabled_reason(state, action_id)
    if reason: raise ValueError(reason)
    action = WORLD['actions'][action_id]
    if set(payload) - ({'code'} if 'code' in action else set()): raise ValueError('UNKNOWN_PAYLOAD')
    if 'code' in action and (not isinstance(payload.get('code'), str) or len(payload['code']) > 12): raise ValueError('Потрібен чотиризначний код із квитанції')
    result = deepcopy(state)
    if 'code' in action and payload['code'] != action['code']:
        result['sim_time'] += 1
        result['note'] = 'Код не підійшов. Поглянь на квитанцію біля табло SBB. Замок не заблоковано.'
    else:
        result['sim_time'] += action['minutes']
        result['energy'] = min(100, max(0, result['energy'] + action['energy']))
        result['cash_cents'] -= action.get('cost', 0)
        if action.get('item') and action['item'] not in result['items']: result['items'].append(action['item'])
        if action.get('item') == 'ticket' and 'ticket_owned' not in result['flags']: result['flags'].append('ticket_owned')
        if action.get('flag') and action['flag'] not in result['flags']: result['flags'].append(action['flag'])
        if action.get('to'):
            result['location'] = action['to']
            if action['to'] not in result['visited']: result['visited'].append(action['to'])
        result['note'] = action['note']
        if action.get('ending'):
            ending = 'honest' if action['ending'] == 'honest' else 'late' if result['sim_time'] > WORLD['deadline'] else 'prepared'
            result['ending'] = {'id':ending, 'title':{'honest':'Чесна друга спроба','late':'Місто зачекало','prepared':'Показ, який відбувся'}[ending],
                'text':{'honest':'Ти зберіг довіру, визнавши межі готовності. Наступного разу — з перевіреним прототипом.',
                    'late':'Ти прийшов пізніше, але показав перевірений результат. Ада залишає час для наступної розмови.',
                    'prepared':'Ти дістався вчасно, перевірив прототип і показав його Аді. Жодних обіцянок мільйонів — одна справжня розмова в цій вигаданій історії.'}[ending]}
    result['history'].append({'action':action_id, 'payload':deepcopy(payload)})
    result['log'] = (result['log'] + [result['note']])[-16:]
    return result


def save_packet(state):
    packet = {'schema':'argon.save.v1', 'world_hash':WORLD_HASH, 'actions':deepcopy(state['history'])}
    return {**packet, 'sha256':digest(packet)}


def restore(packet):
    if not isinstance(packet, dict) or set(packet) != {'schema','world_hash','actions','sha256'}: raise ValueError('SAVE_SCHEMA_INVALID')
    if packet['schema'] != 'argon.save.v1' or packet['world_hash'] != WORLD_HASH: raise ValueError('SAVE_VERSION_UNSUPPORTED')
    if not isinstance(packet['actions'], list) or len(packet['actions']) > MAX_ACTIONS: raise ValueError('SAVE_TOO_LARGE')
    if digest({k:v for k,v in packet.items() if k != 'sha256'}) != packet['sha256']: raise ValueError('SAVE_INTEGRITY_FAILED')
    state = initial_state()
    for entry in packet['actions']:
        if not isinstance(entry, dict) or set(entry) != {'action','payload'}: raise ValueError('SAVE_ACTION_INVALID')
        state = step(state, entry['action'], entry['payload'])
    return state


class Game:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.store = Store(self.directory, initial_state())
        if self.store.state.get('schema') != 'argon.game.v1' or self.store.state.get('world_hash') != WORLD_HASH:
            self.store.close()
            raise ValueError('SAVE_WORLD_CHANGED_MIGRATION_REQUIRED')

    def view(self):
        state = self.store.get()
        location = deepcopy(WORLD['locations'][state['location']])
        for spot in location['hotspots']:
            spot['choices'] = [{**WORLD['actions'][a], 'id':a, 'disabled':disabled_reason(state,a)} for a in spot.pop('actions')]
            # Lock codes belong in explicit clues, not in interaction metadata.
            for choice in spot['choices']: choice.pop('code', None)
        return {'state':state, 'location':location, 'items':WORLD['items'], 'deadline':WORLD['deadline'],
                'saved_checkpoint':(self.directory/'checkpoint.json').is_file()}

    def command(self, action, payload, request_id, expected_revision=None):
        if not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,80}',request_id): raise ValueError('INVALID_REQUEST_ID')
        if not isinstance(payload,dict): raise ValueError('INVALID_PAYLOAD')
        fingerprint = digest([action,payload])
        with self.store.lock:
            old = self.store.duplicate(request_id, fingerprint)
            if old is not None: return old
            before = self.store.get()
            if expected_revision is not None and (type(expected_revision) is not int or expected_revision != before['revision']):
                raise ValueError('REVISION_CONFLICT')
            if action == 'new_game':
                if payload: raise ValueError('UNKNOWN_PAYLOAD')
                after = initial_state()
            elif action == 'load_checkpoint':
                if payload: raise ValueError('UNKNOWN_PAYLOAD')
                path = self.directory/'checkpoint.json'
                if not path.is_file(): raise ValueError('Ще немає ручного збереження')
                if path.stat().st_size > 256000: raise ValueError('SAVE_TOO_LARGE')
                after = restore(json.loads(path.read_text(encoding='utf-8')))
            elif action == 'save_checkpoint':
                if payload: raise ValueError('UNKNOWN_PAYLOAD')
                atomic_write(self.directory/'checkpoint.json', canonical(save_packet(before)).encode('utf-8'))
                after = deepcopy(before)
            else:
                after = step(before,action,payload)
            result = {'accepted':True, 'revision':before['revision']+1, 'request_id':request_id}
            self.store.commit('argon.'+action, payload, 'argon-ui', request_id, result, after, fingerprint)
            return result

    def close(self): self.store.close()
