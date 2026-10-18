# Sovereign source reader: 04-economics, part 1

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## simulation-core/game-forge/sim/__init__.py

Original bytes: 61; SHA256: `e3c93911a13818eada06fc2043ace11ed6420bf2f9422b789818913a52c6f12e`. Original source line numbers follow.

````text
    1 | """Offline, engine-independent Chapter 1 life simulation."""
````

## simulation-core/game-forge/sim/core.py

Original bytes: 14486; SHA256: `8b9e5fca3a0f2854182fb03512a4294b9230c8cfb683cb9b08bc23172ab1c931`. Original source line numbers follow.

````text
    1 | """Pure 15-minute transition. Only stdlib; no I/O or mutable module state in step.
    2 |
    3 | params is the unwrapped dictionary from load_params. rng is a uint32 seed/state;
    4 | the successor is returned as state['rng']. No input is mutated.
    5 | """
    6 | from copy import deepcopy
    7 | import json
    8 | import math
    9 | from pathlib import Path
   10 |
   11 |
   12 | def load_params(path=None):
   13 |     path = Path(path) if path is not None else Path(__file__).with_name('params.json')
   14 |     raw = json.loads(path.read_text(encoding='utf-8'))
   15 |     def unpack(node):
   16 |         if isinstance(node, dict):
   17 |             if 'value' in node:
   18 |                 value = node['value']
   19 |                 lo, hi = node['corridor']
   20 |                 if (isinstance(value, bool) or not isinstance(value, (int, float))
   21 |                         or not math.isfinite(value) or not lo <= value <= hi
   22 |                         or not node['unit'] or node['source'] not in raw['sources']):
   23 |                     raise ValueError('Invalid parameter metadata/value')
   24 |                 if (node['unit'] in ('count', 'uint32', 'rappen', 'rappen/tick',
   25 |                                      'rappen/day', 'rappen/payment', 'game day', 'day',
   26 |                                      'minute', 'minute/hour', 'hour/day')
   27 |                         and type(value) is not int):
   28 |                     raise ValueError('Discrete parameter must be an integer')
   29 |                 return value
   30 |             return {k: unpack(v) for k, v in node.items()}
   31 |         if isinstance(node, list):
   32 |             return [unpack(v) for v in node]
   33 |         if isinstance(node, (int, float)) and not isinstance(node, bool):
   34 |             raise ValueError('Numeric parameter without provenance')
   35 |         return node
   36 |     p = unpack(raw)
   37 |     validate_params(p)
   38 |     return p
   39 |
   40 |
   41 | def validate_params(p):
   42 |     """Cross-field constraints in addition to each leaf's allowed corridor."""
   43 |     c = p['clock']
   44 |     if c['step_minutes'] != 15 or c['hours_per_day'] * c['minutes_per_hour'] % c['step_minutes']:
   45 |         raise ValueError('Clock must use integral 15-minute ticks')
   46 |     starts = [x['start_hour'] for x in c['phases']]
   47 |     if starts[0] != 0 or starts != sorted(set(starts)):
   48 |         raise ValueError('Phases must cover a day in increasing order')
   49 |     if not 0 < p['light']['start_hour'] < p['light']['end_hour'] <= c['hours_per_day']:
   50 |         raise ValueError('Invalid light window')
   51 |     if not 0 < p['habits']['asymptote_fraction'] < 1 or p['habits']['days_to_automaticity'] <= 0:
   52 |         raise ValueError('Invalid automaticity')
   53 |     if p['skills']['level_thresholds'] != sorted(set(p['skills']['level_thresholds'])):
   54 |         raise ValueError('Skill thresholds must increase')
   55 |     for spec in p['scenarios'].values():
   56 |         end = 0
   57 |         for block in spec['schedule']:
   58 |             if block['start'] != end or block['end'] <= end or block['action'] not in p['actions']:
   59 |                 raise ValueError('Schedule has a gap, overlap or unknown action')
   60 |             end = block['end']
   61 |         if end != c['hours_per_day']:
   62 |             raise ValueError('Schedule must cover full day')
   63 |     for a in p['actions'].values():
   64 |         if a['habit'] is not None and a['habit'] not in p['habits']['definitions']:
   65 |             raise ValueError('Unknown habit')
   66 |         if a['skill'] is not None and a['skill'] not in p['skills']['names']:
   67 |             raise ValueError('Unknown skill')
   68 |         if any(k not in p['skills']['names'] for k in a['skill_options']):
   69 |             raise ValueError('Unknown skill option')
   70 |
   71 |
   72 | def clamp(x):
   73 |     return min(1.0, max(0.0, x))
   74 |
   75 |
   76 | def ticks_per_day(p):
   77 |     c = p['clock']
   78 |     return c['hours_per_day'] * c['minutes_per_hour'] // c['step_minutes']
   79 |
   80 |
   81 | def time_fields(tick, p):
   82 |     c = p['clock']
   83 |     days, slot = divmod(tick, ticks_per_day(p))
   84 |     hour = slot * c['step_minutes'] / c['minutes_per_hour']
   85 |     phase = next(x['name'] for x in reversed(c['phases']) if hour >= x['start_hour'])
   86 |     return dict(day=days + 1, week=days // c['days_per_week'] + 1,
   87 |                 season=c['seasons'][(days // c['days_per_season']) % len(c['seasons'])],
   88 |                 phase=phase, hour=hour)
   89 |
   90 |
   91 | def habit_alpha(p):
   92 |     h = p['habits']
   93 |     return 1 - (1 - h['asymptote_fraction']) ** (1 / h['days_to_automaticity'])
   94 |
   95 |
   96 | def habit_step(h, alpha, repetitions=1.0):
   97 |     return 1 - (1 - h) * (1 - alpha) ** repetitions
   98 |
   99 |
  100 | def habit_closed(h0, alpha, repetitions):
  101 |     return 1 - (1 - h0) * math.exp(repetitions * math.log1p(-alpha))
  102 |
  103 |
  104 | def skill_value(hours, p):
  105 |     s = p['skills']
  106 |     return 1 - (1 + hours / s['scale_hours']) ** (-s['exponent'])
  107 |
  108 |
  109 | def skill_level(value, p):
  110 |     return sum(value >= x for x in p['skills']['level_thresholds']) - 1
  111 |
  112 |
  113 | def habit_labels(state, p):
  114 |     return [p['habits']['definitions'][k]['label'] for k, streak in state['habit_streak'].items()
  115 |             if streak >= p['habits']['label_streak_days']]
  116 |
  117 |
  118 | def next_random(rng, p):
  119 |     r = p['rng']
  120 |     if type(rng) is not int or not 0 <= rng < r['modulus']:
  121 |         raise ValueError('rng must be a uint32 integer')
  122 |     successor = (r['multiplier'] * rng + r['increment']) % r['modulus']
  123 |     return successor, successor / r['modulus']
  124 |
  125 |
  126 | def initial_state(p, seed=None, weather=None):
  127 |     seed = p['validation']['seed'] if seed is None else seed
  128 |     next_random(seed, p)
  129 |     i = p['initial']
  130 |     s = dict(tick=0, energy=i['energy'], burnout=i['burnout'], mood=i['mood'],
  131 |              weather=i['weather'] if weather is None else weather, rng=seed,
  132 |              balance_cents=i['balance_cents'], net_cents=0,
  133 |              habits={k: i['habit'] for k in p['habits']['definitions']},
  134 |              habit_dose={k: 0.0 for k in p['habits']['definitions']},
  135 |              habit_streak={k: 0 for k in p['habits']['definitions']},
  136 |              practice_hours={k: i['practice_hours'] for k in p['skills']['names']},
  137 |              pending_energy=0.0, pending_burnout=0.0,
  138 |              transactions=[], events=[], requested_action=None, effective_action=None)
  139 |     validate_state(s, p)
  140 |     return s
  141 |
  142 |
  143 | def validate_state(s, p):
  144 |     def finite(x):
  145 |         return type(x) in (int, float) and math.isfinite(x)
  146 |     if type(s['tick']) is not int or s['tick'] < 0:
  147 |         raise ValueError('Invalid tick')
  148 |     for name in ('energy', 'burnout', 'mood'):
  149 |         if not finite(s[name]) or not 0 <= s[name] <= 1:
  150 |             raise ValueError('Invalid normalized state: ' + name)
  151 |     for name in ('habits', 'habit_dose'):
  152 |         if set(s[name]) != set(p['habits']['definitions']):
  153 |             raise ValueError('Invalid habit keys')
  154 |         if any(not finite(x) or not 0 <= x <= 1 for x in s[name].values()):
  155 |             raise ValueError('Invalid habit state')
  156 |     if set(s['habit_streak']) != set(p['habits']['definitions']) or any(
  157 |             type(x) is not int or x < 0 for x in s['habit_streak'].values()):
  158 |         raise ValueError('Invalid streak')
  159 |     if set(s['practice_hours']) != set(p['skills']['names']) or any(
  160 |             not finite(x) or x < 0 for x in s['practice_hours'].values()):
  161 |         raise ValueError('Invalid practice hours')
  162 |     for name in ('pending_energy', 'pending_burnout'):
  163 |         if not finite(s[name]):
  164 |             raise ValueError('Invalid pending effect')
  165 |     if s['weather'] not in p['weather']:
  166 |         raise ValueError('Unknown weather')
  167 |     for name in ('balance_cents', 'net_cents'):
  168 |         if type(s[name]) is not int:
  169 |             raise ValueError('Money must be integer rappen')
  170 |     if s['balance_cents'] != p['initial']['balance_cents'] + s['net_cents']:
  171 |         raise ValueError('Balance does not reconcile')
  172 |     next_random(s['rng'], p)
  173 |
  174 |
  175 | def weather_shifts(weather, hour, light, p):
  176 |     l = p['light']
  177 |     compensation = l['negative_weather_compensation'] if light and l['start_hour'] <= hour < l['end_hour'] else 0
  178 |     return tuple(v * (1 - compensation) if v < 0 else v
  179 |                  for v in (p['weather'][weather]['energy_shift'], p['weather'][weather]['mood_shift']))
  180 |
  181 |
  182 | def energy_equilibrium(action, burnout, weather, hour, light, p):
  183 |     """Fixed environment/burnout equilibrium; not a claim of whole-life equilibrium."""
  184 |     if action == 'sleep':
  185 |         return p['actions'][action]['energy_target']
  186 |     shift, _ = weather_shifts(weather, hour, light, p)
  187 |     return clamp(p['actions'][action]['energy_target'] + shift - p['energy']['burnout_penalty'] * burnout)
  188 |
  189 |
  190 | def energy_step(energy, action, burnout, weather, hour, light, quality, p):
  191 |     dt = p['clock']['step_minutes'] / p['clock']['minutes_per_hour']
  192 |     rate = p['energy']['sleep_rate_per_hour'] * quality if action == 'sleep' else p['energy']['awake_rate_per_hour']
  193 |     target = energy_equilibrium(action, burnout, weather, hour, light, p)
  194 |     return target + (energy - target) * math.exp(-rate * dt)
  195 |
  196 |
  197 | def step(state, action, params, rng):
  198 |     """One tick; blocked actions consume time as rest with an explicit reason.
  199 |
  200 |     action: kind; optional weather (day boundary only), light: bool,
  201 |     sleep_quality: [0,1], skill: allowed training target, allow_debt: bool, transactions: list of
  202 |     {id: str, amount_cents: int}. Transfers are per invocation, not idempotent.
  203 |     """
  204 |     p = params
  205 |     validate_state(state, p)
  206 |     allowed = {'kind', 'weather', 'light', 'sleep_quality', 'skill', 'allow_debt', 'transactions'}
  207 |     if not isinstance(action, dict) or set(action) - allowed or action.get('kind') not in p['actions']:
  208 |         raise ValueError('Unknown action or field')
  209 |     if 'skill' in action and action['skill'] not in p['actions'][action['kind']]['skill_options']:
  210 |         raise ValueError('Skill not allowed for this action')
  211 |     for name in ('light', 'allow_debt'):
  212 |         if name in action and type(action[name]) is not bool:
  213 |             raise ValueError('Expected bool: ' + name)
  214 |     quality = action.get('sleep_quality', 1.0)
  215 |     if type(quality) not in (int, float) or not math.isfinite(quality) or not 0 <= quality <= 1:
  216 |         raise ValueError('Invalid sleep quality')
  217 |     transfers = action.get('transactions', [])
  218 |     if not isinstance(transfers, list):
  219 |         raise ValueError('Transactions must be a list')
  220 |     for t in transfers:
  221 |         if not isinstance(t, dict) or set(t) != {'id', 'amount_cents'} or not isinstance(t['id'], str) or not t['id'] or type(t['amount_cents']) is not int:
  222 |             raise ValueError('Invalid transaction')
  223 |     s = deepcopy(state)
  224 |     s['transactions'], s['events'] = [], []
  225 |     s['rng'], draw = next_random(rng, p)
  226 |     if 'weather' in action:
  227 |         if action['weather'] not in p['weather']:
  228 |             raise ValueError('Unknown weather')
  229 |         if s['tick'] % ticks_per_day(p) and action['weather'] != s['weather']:
  230 |             raise ValueError('Weather is a daily input; change only at midnight')
  231 |         s['weather'] = action['weather']
  232 |     def transact(name, amount):
  233 |         before = s['balance_cents']
  234 |         after = before + amount
  235 |         if amount < 0 and after < 0 and not action.get('allow_debt', False):
  236 |             s['events'].append({'type': 'insufficient_funds', 'id': name})
  237 |             return False
  238 |         s['balance_cents'] = after
  239 |         s['net_cents'] += amount
  240 |         s['transactions'].append({'id': name, 'amount_cents': amount})
  241 |         if after < 0 and after < before:
  242 |             s['events'].append({'type': 'debt', 'id': name, 'amount_cents': max(0, -after) - max(0, -before)})
  243 |         return True
  244 |     kind = action['kind']
  245 |     a = p['actions'][kind]
  246 |     reason = None
  247 |     if s['energy'] < a['minimum_energy']:
  248 |         reason = 'low_energy'
  249 |     elif a['burnout_locked'] and s['burnout'] >= p['burnout']['threshold']:
  250 |         reason = 'burnout'
  251 |     elif draw < clamp(a['failure_base'] + a['failure_burnout_factor'] * s['burnout']):
  252 |         reason = 'motivation'
  253 |     elif a['cost_cents'] and not transact('action:' + kind, -a['cost_cents']):
  254 |         reason = 'insufficient_funds'
  255 |     if reason:
  256 |         s['events'].append({'type': 'blocked', 'action': kind, 'reason': reason})
  257 |         kind = 'rest'
  258 |         a = p['actions'][kind]
  259 |     s['requested_action'], s['effective_action'] = action['kind'], kind
  260 |     if a['wage_cents']:
  261 |         transact('wage:' + kind, a['wage_cents'])
  262 |     for t in transfers:
  263 |         transact(t['id'], t['amount_cents'])
  264 |     dt = p['clock']['step_minutes'] / p['clock']['minutes_per_hour']
  265 |     hour = time_fields(s['tick'], p)['hour']
  266 |     old_energy, old_burnout = s['energy'], s['burnout']
  267 |     s['energy'] = clamp(energy_step(old_energy, kind, old_burnout, s['weather'], hour, action.get('light', False), quality, p))
  268 |     b = p['burnout']
  269 |     load = clamp(a['load'] + (b['low_energy_load'] if old_energy < b['low_energy_threshold'] and kind != 'sleep' else 0))
  270 |     s['burnout'] = clamp(old_burnout + dt * (b['accumulation_per_hour'] * load - b['recovery_per_hour'] * a['recovery'] * old_burnout))
  271 |     _, mood_shift = weather_shifts(s['weather'], hour, action.get('light', False), p)
  272 |     mood_target = clamp(a['mood_target'] + mood_shift - p['mood']['burnout_penalty'] * old_burnout)
  273 |     s['mood'] = mood_target + (s['mood'] - mood_target) * math.exp(-p['mood']['rate_per_hour'] * dt)
  274 |     habit = a['habit']
  275 |     if habit is not None:
  276 |         dose = min(1 - s['habit_dose'][habit], dt / p['habits']['definitions'][habit]['dose_hours'])
  277 |         s['habit_dose'][habit] += dose
  278 |         s['habits'][habit] = habit_step(s['habits'][habit], habit_alpha(p), dose)
  279 |         s['pending_energy'] += dose * a['morning_energy']
  280 |         s['pending_burnout'] += dose * a['morning_burnout']
  281 |         s['burnout'] = clamp(s['burnout'] + dose * a['immediate_burnout'])
  282 |     if a['skill'] is not None:
  283 |         s['practice_hours'][action.get('skill', a['skill'])] += dt * old_energy * (1 - old_burnout)
  284 |     s['tick'] += 1
  285 |     next_hour = time_fields(s['tick'], p)['hour']
  286 |     morning = next(x['start_hour'] for x in p['clock']['phases'] if x['name'] == 'morning')
  287 |     if next_hour == morning:
  288 |         s['energy'] = clamp(s['energy'] + s['pending_energy'])
  289 |         s['burnout'] = clamp(s['burnout'] + s['pending_burnout'])
  290 |         s['pending_energy'], s['pending_burnout'] = 0.0, 0.0
  291 |         s['events'].append({'type': 'morning'})
  292 |     if s['tick'] % ticks_per_day(p) == 0:
  293 |         days = s['tick'] // ticks_per_day(p)
  294 |         if days % p['money']['support_period_days'] == 0:
  295 |             transact('social_support', p['money']['support_cents'])
  296 |         transact('daily_living', -p['money']['daily_cost_cents'])
  297 |         for h in s['habits']:
  298 |             full = s['habit_dose'][h] >= 1 - p['validation']['tolerance']
  299 |             s['habit_streak'][h] = s['habit_streak'][h] + 1 if full else 0
  300 |             s['habit_dose'][h] = 0.0
  301 |     validate_state(s, p)
  302 |     return s
````
