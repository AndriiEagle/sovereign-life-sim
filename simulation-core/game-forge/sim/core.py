"""Pure 15-minute transition. Only stdlib; no I/O or mutable module state in step.

params is the unwrapped dictionary from load_params. rng is a uint32 seed/state;
the successor is returned as state['rng']. No input is mutated.
"""
from copy import deepcopy
import json
import math
from pathlib import Path


def load_params(path=None):
    path = Path(path) if path is not None else Path(__file__).with_name('params.json')
    raw = json.loads(path.read_text(encoding='utf-8'))
    def unpack(node):
        if isinstance(node, dict):
            if 'value' in node:
                value = node['value']
                lo, hi = node['corridor']
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or not lo <= value <= hi
                        or not node['unit'] or node['source'] not in raw['sources']):
                    raise ValueError('Invalid parameter metadata/value')
                if (node['unit'] in ('count', 'uint32', 'rappen', 'rappen/tick',
                                     'rappen/day', 'rappen/payment', 'game day', 'day',
                                     'minute', 'minute/hour', 'hour/day')
                        and type(value) is not int):
                    raise ValueError('Discrete parameter must be an integer')
                return value
            return {k: unpack(v) for k, v in node.items()}
        if isinstance(node, list):
            return [unpack(v) for v in node]
        if isinstance(node, (int, float)) and not isinstance(node, bool):
            raise ValueError('Numeric parameter without provenance')
        return node
    p = unpack(raw)
    validate_params(p)
    return p


def validate_params(p):
    """Cross-field constraints in addition to each leaf's allowed corridor."""
    c = p['clock']
    if c['step_minutes'] != 15 or c['hours_per_day'] * c['minutes_per_hour'] % c['step_minutes']:
        raise ValueError('Clock must use integral 15-minute ticks')
    starts = [x['start_hour'] for x in c['phases']]
    if starts[0] != 0 or starts != sorted(set(starts)):
        raise ValueError('Phases must cover a day in increasing order')
    if not 0 < p['light']['start_hour'] < p['light']['end_hour'] <= c['hours_per_day']:
        raise ValueError('Invalid light window')
    if not 0 < p['habits']['asymptote_fraction'] < 1 or p['habits']['days_to_automaticity'] <= 0:
        raise ValueError('Invalid automaticity')
    if p['skills']['level_thresholds'] != sorted(set(p['skills']['level_thresholds'])):
        raise ValueError('Skill thresholds must increase')
    for spec in p['scenarios'].values():
        end = 0
        for block in spec['schedule']:
            if block['start'] != end or block['end'] <= end or block['action'] not in p['actions']:
                raise ValueError('Schedule has a gap, overlap or unknown action')
            end = block['end']
        if end != c['hours_per_day']:
            raise ValueError('Schedule must cover full day')
    for a in p['actions'].values():
        if a['habit'] is not None and a['habit'] not in p['habits']['definitions']:
            raise ValueError('Unknown habit')
        if a['skill'] is not None and a['skill'] not in p['skills']['names']:
            raise ValueError('Unknown skill')
        if any(k not in p['skills']['names'] for k in a['skill_options']):
            raise ValueError('Unknown skill option')


def clamp(x):
    return min(1.0, max(0.0, x))


def ticks_per_day(p):
    c = p['clock']
    return c['hours_per_day'] * c['minutes_per_hour'] // c['step_minutes']


def time_fields(tick, p):
    c = p['clock']
    days, slot = divmod(tick, ticks_per_day(p))
    hour = slot * c['step_minutes'] / c['minutes_per_hour']
    phase = next(x['name'] for x in reversed(c['phases']) if hour >= x['start_hour'])
    return dict(day=days + 1, week=days // c['days_per_week'] + 1,
                season=c['seasons'][(days // c['days_per_season']) % len(c['seasons'])],
                phase=phase, hour=hour)


def habit_alpha(p):
    h = p['habits']
    return 1 - (1 - h['asymptote_fraction']) ** (1 / h['days_to_automaticity'])


def habit_step(h, alpha, repetitions=1.0):
    return 1 - (1 - h) * (1 - alpha) ** repetitions


def habit_closed(h0, alpha, repetitions):
    return 1 - (1 - h0) * math.exp(repetitions * math.log1p(-alpha))


def skill_value(hours, p):
    s = p['skills']
    return 1 - (1 + hours / s['scale_hours']) ** (-s['exponent'])


def skill_level(value, p):
    return sum(value >= x for x in p['skills']['level_thresholds']) - 1


def habit_labels(state, p):
    return [p['habits']['definitions'][k]['label'] for k, streak in state['habit_streak'].items()
            if streak >= p['habits']['label_streak_days']]


def next_random(rng, p):
    r = p['rng']
    if type(rng) is not int or not 0 <= rng < r['modulus']:
        raise ValueError('rng must be a uint32 integer')
    successor = (r['multiplier'] * rng + r['increment']) % r['modulus']
    return successor, successor / r['modulus']


def initial_state(p, seed=None, weather=None):
    seed = p['validation']['seed'] if seed is None else seed
    next_random(seed, p)
    i = p['initial']
    s = dict(tick=0, energy=i['energy'], burnout=i['burnout'], mood=i['mood'],
             weather=i['weather'] if weather is None else weather, rng=seed,
             balance_cents=i['balance_cents'], net_cents=0,
             habits={k: i['habit'] for k in p['habits']['definitions']},
             habit_dose={k: 0.0 for k in p['habits']['definitions']},
             habit_streak={k: 0 for k in p['habits']['definitions']},
             practice_hours={k: i['practice_hours'] for k in p['skills']['names']},
             pending_energy=0.0, pending_burnout=0.0,
             transactions=[], events=[], requested_action=None, effective_action=None)
    validate_state(s, p)
    return s


def validate_state(s, p):
    def finite(x):
        return type(x) in (int, float) and math.isfinite(x)
    if type(s['tick']) is not int or s['tick'] < 0:
        raise ValueError('Invalid tick')
    for name in ('energy', 'burnout', 'mood'):
        if not finite(s[name]) or not 0 <= s[name] <= 1:
            raise ValueError('Invalid normalized state: ' + name)
    for name in ('habits', 'habit_dose'):
        if set(s[name]) != set(p['habits']['definitions']):
            raise ValueError('Invalid habit keys')
        if any(not finite(x) or not 0 <= x <= 1 for x in s[name].values()):
            raise ValueError('Invalid habit state')
    if set(s['habit_streak']) != set(p['habits']['definitions']) or any(
            type(x) is not int or x < 0 for x in s['habit_streak'].values()):
        raise ValueError('Invalid streak')
    if set(s['practice_hours']) != set(p['skills']['names']) or any(
            not finite(x) or x < 0 for x in s['practice_hours'].values()):
        raise ValueError('Invalid practice hours')
    for name in ('pending_energy', 'pending_burnout'):
        if not finite(s[name]):
            raise ValueError('Invalid pending effect')
    if s['weather'] not in p['weather']:
        raise ValueError('Unknown weather')
    for name in ('balance_cents', 'net_cents'):
        if type(s[name]) is not int:
            raise ValueError('Money must be integer rappen')
    if s['balance_cents'] != p['initial']['balance_cents'] + s['net_cents']:
        raise ValueError('Balance does not reconcile')
    next_random(s['rng'], p)


def weather_shifts(weather, hour, light, p):
    l = p['light']
    compensation = l['negative_weather_compensation'] if light and l['start_hour'] <= hour < l['end_hour'] else 0
    return tuple(v * (1 - compensation) if v < 0 else v
                 for v in (p['weather'][weather]['energy_shift'], p['weather'][weather]['mood_shift']))


def energy_equilibrium(action, burnout, weather, hour, light, p):
    """Fixed environment/burnout equilibrium; not a claim of whole-life equilibrium."""
    if action == 'sleep':
        return p['actions'][action]['energy_target']
    shift, _ = weather_shifts(weather, hour, light, p)
    return clamp(p['actions'][action]['energy_target'] + shift - p['energy']['burnout_penalty'] * burnout)


def energy_step(energy, action, burnout, weather, hour, light, quality, p):
    dt = p['clock']['step_minutes'] / p['clock']['minutes_per_hour']
    rate = p['energy']['sleep_rate_per_hour'] * quality if action == 'sleep' else p['energy']['awake_rate_per_hour']
    target = energy_equilibrium(action, burnout, weather, hour, light, p)
    return target + (energy - target) * math.exp(-rate * dt)


def step(state, action, params, rng):
    """One tick; blocked actions consume time as rest with an explicit reason.

    action: kind; optional weather (day boundary only), light: bool,
    sleep_quality: [0,1], skill: allowed training target, allow_debt: bool, transactions: list of
    {id: str, amount_cents: int}. Transfers are per invocation, not idempotent.
    """
    p = params
    validate_state(state, p)
    allowed = {'kind', 'weather', 'light', 'sleep_quality', 'skill', 'allow_debt', 'transactions'}
    if not isinstance(action, dict) or set(action) - allowed or action.get('kind') not in p['actions']:
        raise ValueError('Unknown action or field')
    if 'skill' in action and action['skill'] not in p['actions'][action['kind']]['skill_options']:
        raise ValueError('Skill not allowed for this action')
    for name in ('light', 'allow_debt'):
        if name in action and type(action[name]) is not bool:
            raise ValueError('Expected bool: ' + name)
    quality = action.get('sleep_quality', 1.0)
    if type(quality) not in (int, float) or not math.isfinite(quality) or not 0 <= quality <= 1:
        raise ValueError('Invalid sleep quality')
    transfers = action.get('transactions', [])
    if not isinstance(transfers, list):
        raise ValueError('Transactions must be a list')
    for t in transfers:
        if not isinstance(t, dict) or set(t) != {'id', 'amount_cents'} or not isinstance(t['id'], str) or not t['id'] or type(t['amount_cents']) is not int:
            raise ValueError('Invalid transaction')
    s = deepcopy(state)
    s['transactions'], s['events'] = [], []
    s['rng'], draw = next_random(rng, p)
    if 'weather' in action:
        if action['weather'] not in p['weather']:
            raise ValueError('Unknown weather')
        if s['tick'] % ticks_per_day(p) and action['weather'] != s['weather']:
            raise ValueError('Weather is a daily input; change only at midnight')
        s['weather'] = action['weather']
    def transact(name, amount):
        before = s['balance_cents']
        after = before + amount
        if amount < 0 and after < 0 and not action.get('allow_debt', False):
            s['events'].append({'type': 'insufficient_funds', 'id': name})
            return False
        s['balance_cents'] = after
        s['net_cents'] += amount
        s['transactions'].append({'id': name, 'amount_cents': amount})
        if after < 0 and after < before:
            s['events'].append({'type': 'debt', 'id': name, 'amount_cents': max(0, -after) - max(0, -before)})
        return True
    kind = action['kind']
    a = p['actions'][kind]
    reason = None
    if s['energy'] < a['minimum_energy']:
        reason = 'low_energy'
    elif a['burnout_locked'] and s['burnout'] >= p['burnout']['threshold']:
        reason = 'burnout'
    elif draw < clamp(a['failure_base'] + a['failure_burnout_factor'] * s['burnout']):
        reason = 'motivation'
    elif a['cost_cents'] and not transact('action:' + kind, -a['cost_cents']):
        reason = 'insufficient_funds'
    if reason:
        s['events'].append({'type': 'blocked', 'action': kind, 'reason': reason})
        kind = 'rest'
        a = p['actions'][kind]
    s['requested_action'], s['effective_action'] = action['kind'], kind
    if a['wage_cents']:
        transact('wage:' + kind, a['wage_cents'])
    for t in transfers:
        transact(t['id'], t['amount_cents'])
    dt = p['clock']['step_minutes'] / p['clock']['minutes_per_hour']
    hour = time_fields(s['tick'], p)['hour']
    old_energy, old_burnout = s['energy'], s['burnout']
    s['energy'] = clamp(energy_step(old_energy, kind, old_burnout, s['weather'], hour, action.get('light', False), quality, p))
    b = p['burnout']
    load = clamp(a['load'] + (b['low_energy_load'] if old_energy < b['low_energy_threshold'] and kind != 'sleep' else 0))
    s['burnout'] = clamp(old_burnout + dt * (b['accumulation_per_hour'] * load - b['recovery_per_hour'] * a['recovery'] * old_burnout))
    _, mood_shift = weather_shifts(s['weather'], hour, action.get('light', False), p)
    mood_target = clamp(a['mood_target'] + mood_shift - p['mood']['burnout_penalty'] * old_burnout)
    s['mood'] = mood_target + (s['mood'] - mood_target) * math.exp(-p['mood']['rate_per_hour'] * dt)
    habit = a['habit']
    if habit is not None:
        dose = min(1 - s['habit_dose'][habit], dt / p['habits']['definitions'][habit]['dose_hours'])
        s['habit_dose'][habit] += dose
        s['habits'][habit] = habit_step(s['habits'][habit], habit_alpha(p), dose)
        s['pending_energy'] += dose * a['morning_energy']
        s['pending_burnout'] += dose * a['morning_burnout']
        s['burnout'] = clamp(s['burnout'] + dose * a['immediate_burnout'])
    if a['skill'] is not None:
        s['practice_hours'][action.get('skill', a['skill'])] += dt * old_energy * (1 - old_burnout)
    s['tick'] += 1
    next_hour = time_fields(s['tick'], p)['hour']
    morning = next(x['start_hour'] for x in p['clock']['phases'] if x['name'] == 'morning')
    if next_hour == morning:
        s['energy'] = clamp(s['energy'] + s['pending_energy'])
        s['burnout'] = clamp(s['burnout'] + s['pending_burnout'])
        s['pending_energy'], s['pending_burnout'] = 0.0, 0.0
        s['events'].append({'type': 'morning'})
    if s['tick'] % ticks_per_day(p) == 0:
        days = s['tick'] // ticks_per_day(p)
        if days % p['money']['support_period_days'] == 0:
            transact('social_support', p['money']['support_cents'])
        transact('daily_living', -p['money']['daily_cost_cents'])
        for h in s['habits']:
            full = s['habit_dose'][h] >= 1 - p['validation']['tolerance']
            s['habit_streak'][h] = s['habit_streak'][h] + 1 if full else 0
            s['habit_dose'][h] = 0.0
    validate_state(s, p)
    return s
