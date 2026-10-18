# Sovereign source reader: 02-state, part 1

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## simulation-core/unified_tick.py

Original bytes: 17557; SHA256: `4f13745e5237ba5136caeb529828aa0aa6eb505d3fb2b8ef5e951033ebadd20b`. Original source line numbers follow.

````text
    1 | """Single pure adapter over the unchanged game-forge and Conductor snapshots."""
    2 | from copy import deepcopy
    3 | from datetime import datetime, timedelta, timezone
    4 | from decimal import Decimal, ROUND_HALF_UP
    5 | import math
    6 | from pathlib import Path
    7 | import sys
    8 |
    9 | sys.path.insert(0, str(Path(__file__).parent / 'game-forge'))
   10 | from sim.core import initial_state as life_initial, load_params, step as life_step
   11 | from revenue_lab.core import Quote, evaluate_quote, money
   12 | from contracts import identifier, keys, number, text
   13 | from game_theory_shield import comparison
   14 |
   15 | PARAMS = load_params()
   16 | COMPLETE = {'SHIPPED','ACTIVE_CASHFLOW'}
   17 |
   18 |
   19 | def timestamp(value):
   20 |     parsed = datetime.fromisoformat(value.replace('Z','+00:00'))
   21 |     if parsed.tzinfo is None: raise ValueError('TIMEZONE_REQUIRED')
   22 |     return parsed.astimezone(timezone.utc)
   23 |
   24 |
   25 | def initial_state(manifest, seed=42, now='2026-10-18T00:00:00+00:00'):
   26 |     timestamp(now)
   27 |     projects = manifest['projects']
   28 |     ordered = [next(p for p in projects if p['id']==id) for id in ('synera','brand-social-os')]
   29 |     ordered += [p for p in projects if p['id'] not in {'synera','brand-social-os'}]
   30 |     nodes = []
   31 |     for i,p in enumerate(ordered):
   32 |         nodes.append(dict(id=p['id'], title=p['title'], manifest_id=p['id'], source_status=p['status'],
   33 |                           status='FOCUSED' if i<2 else 'Queued', wave=1 if i<2 else 2 if i<9 else 3,
   34 |                           kind='tower' if i<2 else 'mine', progress=0., revenue_day_cents=0,
   35 |                           cost_day_cents=0, setup_cents=0, auto_deduct_setup=False,
   36 |                           setup_deducted=False, setup_paid_cents=0, net_cents=0, owner_rule=None))
   37 |     life = life_initial(PARAMS, seed=seed)
   38 |     state = dict(schema='sovereign.state.v2', revision=0, seed=seed, start_time=now, sim_time=now,
   39 |                  life=life, nodes=nodes, selected='synera',
   40 |                  bio=dict(Bio_RAM=80, Sleep_Sync_Index=80, Swiss_Grey_Weather_Modifier=0,
   41 |                           debuff_reason=None, debuff_until_step=None, reduced_fog=False, recovery='Відпочинок'),
   42 |                  config=dict(trust_min=0, trust_max=100, trust_k=.6, gemeinde_deadline=None,
   43 |                              build_per_hour=2, confidence_assumption=50, b2b_uplift_assumption=0,
   44 |                              revenue_multiplier=1),
   45 |                  quest=dict(start_step=None, verified_milestones=[], milestones=['jwt-two-users','neon-recovery']),
   46 |                  rules={}, assets={}, bridge=dict(status='NOT_CONNECTED', providers='NOT_CONNECTED'),
   47 |                  economic_remainder=0., tower_net_cents=0)
   48 |     return refresh(state)
   49 |
   50 |
   51 | def node(state, node_id):
   52 |     identifier(node_id)
   53 |     found = next((n for n in state['nodes'] if n['id']==node_id), None)
   54 |     if not found: raise ValueError('UNKNOWN_NODE')
   55 |     return found
   56 |
   57 |
   58 | def refresh(state):
   59 |     # Additive defaults keep pre-audit journal states usable without rewriting history.
   60 |     state['config'].setdefault('revenue_multiplier',1)
   61 |     for n in state['nodes']:
   62 |         for key,value in dict(auto_deduct_setup=False,setup_deducted=False,setup_paid_cents=0).items():
   63 |             n.setdefault(key,value)
   64 |     state['sim_time'] = (timestamp(state['start_time']) + timedelta(minutes=15*state['life']['tick'])).isoformat()
   65 |     b = state['bio']
   66 |     active = b['debuff_until_step'] is not None and state['life']['tick'] < b['debuff_until_step']
   67 |     b['debuff_active'] = active
   68 |     b['build_multiplier'] = .6 if active else 1.
   69 |     b['fog'] = .12 if b['reduced_fog'] else .48 if active else 0.
   70 |     remaining = state['quest']['start_step']
   71 |     state['quest']['hours_remaining'] = None if remaining is None else max(0, 48-(state['life']['tick']-remaining)/4)
   72 |     cfg = state['config']
   73 |     verified = len(state['quest']['verified_milestones'])
   74 |     trust = cfg['trust_min']+(cfg['trust_max']-cfg['trust_min'])*(1-math.exp(-cfg['trust_k']*verified))
   75 |     deadline = cfg['gemeinde_deadline']
   76 |     cash = state['life']['balance_cents']
   77 |     multiplier=cfg['revenue_multiplier']
   78 |     burn = PARAMS['money']['daily_cost_cents'] + sum(n['cost_day_cents']-scenario_revenue(n,multiplier) for n in state['nodes'] if n['status']=='ACTIVE_CASHFLOW')
   79 |     state['economy'] = dict(status='SYNTHETIC_SCENARIO_NOT_ACTUAL', currency='CHF', cash_cents=cash,
   80 |                            Runway_CHF=money(Decimal(cash)/100), runway_days=round(cash/burn,2) if burn>0 else None,
   81 |                            actual_cash_chf=None, daily_burn_cents=burn, gilbert_trust_index=round(trust,4),
   82 |                            trust_formula='min + (max-min) * (1-exp(-k * verified_milestones))',
   83 |                            gemeinde_days_remaining=None if deadline is None else round((timestamp(deadline)-timestamp(state['sim_time'])).total_seconds()/86400,2),
   84 |                            gemeinde_status='UNCONFIGURED' if deadline is None else 'SCENARIO_DATE',
   85 |                            revenue_multiplier=multiplier, setup_paid_cents=sum(n['setup_paid_cents'] for n in state['nodes']),
   86 |                            ROI={n['id']:round((n['net_cents']-n['setup_paid_cents'])/n['setup_cents'],4) if n['setup_cents'] else None for n in state['nodes']})
   87 |     state['economy']['conductor_nodes']={n['id']:daily_economics(n,multiplier) for n in state['nodes'] if n['status']=='ACTIVE_CASHFLOW'}
   88 |     validate(state)
   89 |     return state
   90 |
   91 |
   92 | def scenario_revenue(n, multiplier=1):
   93 |     return int((Decimal(n['revenue_day_cents'])*Decimal(str(multiplier))).quantize(Decimal(1),rounding=ROUND_HALF_UP))
   94 |
   95 |
   96 | def daily_economics(n, multiplier=1):
   97 |     revenue=scenario_revenue(n,multiplier)
   98 |     if not revenue:
   99 |         return dict(contribution_after_reserve=money(-Decimal(n['cost_day_cents'])/100),status='ZERO_SALES_SCENARIO')
  100 |     return evaluate_quote(Quote.from_mapping(dict(currency='CHF',price=money(Decimal(revenue)/100),
  101 |         fee_rate='0',fee_fixed='0',variable_cost=money(Decimal(n['cost_day_cents'])/100),reserve_rate='0',
  102 |         acquisition_hours='0',delivery_hours='1',support_hours='0',hourly_value='0')))
  103 |
  104 |
  105 | def validate(state):
  106 |     if len({n['id'] for n in state['nodes']}) != len(state['nodes']) or len(state['nodes']) > 100:
  107 |         raise ValueError('NODE_LIMIT_OR_DUPLICATE')
  108 |     if sum(n['status']=='FOCUSED' for n in state['nodes']) > 2:
  109 |         raise ValueError('FOCUS_LIMIT')
  110 |     for n in state['nodes']:
  111 |         identifier(n['id']); text(n['title'])
  112 |         number(n['progress'],'PROGRESS',0,100)
  113 |         for key in ('revenue_day_cents','cost_day_cents','setup_cents','setup_paid_cents'):
  114 |             number(n[key],key,0,100000000,True)
  115 |         for key in ('auto_deduct_setup','setup_deducted'):
  116 |             if type(n[key]) is not bool: raise ValueError('INVALID_BOOLEAN')
  117 |     number(state['config']['revenue_multiplier'],'REVENUE_MULTIPLIER',0,5)
  118 |     for key in ('Bio_RAM','Sleep_Sync_Index'):
  119 |         number(state['bio'][key],key,0,100)
  120 |
  121 |
  122 | def deduct_setup(state, n):
  123 |     """One lifetime debit per tower, retained through edits, rollback and replay."""
  124 |     if not n.get('auto_deduct_setup',False) or n.get('setup_deducted',False): return
  125 |     amount=n['setup_cents']
  126 |     if state['life']['balance_cents'] < amount: raise ValueError('INSUFFICIENT_SCENARIO_FUNDS')
  127 |     state['life']['balance_cents']-=amount; state['life']['net_cents']-=amount
  128 |     n.update(setup_deducted=True,setup_paid_cents=amount)
  129 |
  130 |
  131 | def apply_operations(state, operations, owner, charge=True):
  132 |     if not isinstance(operations,list) or not 1 <= len(operations) <= 8:
  133 |         raise ValueError('INVALID_OPERATIONS')
  134 |     candidate = deepcopy(state)
  135 |     for op in operations:
  136 |         if not isinstance(op,dict): raise ValueError('INVALID_OPERATION')
  137 |         kind = op.get('op')
  138 |         if kind == 'add_node':
  139 |             keys(op,['op','id','title','kind','revenue_day_cents','cost_day_cents','setup_cents','auto_deduct_setup'],['op','id','title'])
  140 |             id = identifier(op['id']); title = text(op['title'])
  141 |             existing = next((n for n in candidate['nodes'] if n['id']==id),None)
  142 |             if existing and existing['owner_rule'] != owner: raise ValueError('NODE_OWNED_ELSEWHERE')
  143 |             if op.get('kind','tower') not in {'tower','mine','agent'}: raise ValueError('INVALID_NODE_KIND')
  144 |             auto=op.get('auto_deduct_setup',False)
  145 |             if type(auto) is not bool: raise ValueError('INVALID_BOOLEAN')
  146 |             fields = dict(title=title, kind=op.get('kind','tower'), auto_deduct_setup=auto,
  147 |                           **{k:number(op.get(k,0),k,0,100000000,True) for k in ('revenue_day_cents','cost_day_cents','setup_cents')})
  148 |             if existing: existing.update(fields)
  149 |             else:
  150 |                 existing=dict(id=id, manifest_id=None, source_status='GENERATED_SCENARIO',
  151 |                     status='Queued', wave=4, progress=0., net_cents=0, owner_rule=owner,
  152 |                     setup_deducted=False,setup_paid_cents=0,**fields)
  153 |                 candidate['nodes'].append(existing)
  154 |             if charge: deduct_setup(candidate,existing)
  155 |         elif kind == 'expense':
  156 |             keys(op,['op','amount_cents','kpi_modifiers'],['op','amount_cents'])
  157 |             amount = number(op['amount_cents'],'EXPENSE',0,100000000,True)
  158 |             modifiers=keys(op.get('kpi_modifiers',{}),['revenue_multiplier','Bio_RAM','confidence_assumption','b2b_uplift_assumption'])
  159 |             modifiers={k:number(v,k,0,5 if k=='revenue_multiplier' else 100) for k,v in modifiers.items()}
  160 |             if charge:
  161 |                 if candidate['life']['balance_cents'] < amount: raise ValueError('INSUFFICIENT_SCENARIO_FUNDS')
  162 |                 candidate['life']['balance_cents'] -= amount; candidate['life']['net_cents'] -= amount
  163 |                 for key,value in modifiers.items():
  164 |                     candidate['bio' if key=='Bio_RAM' else 'config'][key]=value
  165 |         elif kind == 'set_modifier':
  166 |             keys(op,['op','name','value'],['op','name','value'])
  167 |             if op['name'] not in {'confidence_assumption','b2b_uplift_assumption'}: raise ValueError('MODIFIER_NOT_ALLOWED')
  168 |             candidate['config'][op['name']] = number(op['value'],'MODIFIER',0,100)
  169 |         else: raise ValueError('OPERATION_NOT_ALLOWED')
  170 |     return refresh(candidate)
  171 |
  172 |
  173 | def advance(state, steps=4, action='rest', rule_operations=None):
  174 |     number(steps,'STEPS',1,672,True)
  175 |     if action not in {'rest','sleep','work'}: raise ValueError('UNKNOWN_ACTION')
  176 |     result = deepcopy(state)
  177 |     for id, rule in result['rules'].items():
  178 |         pending = rule.get('pending')
  179 |         if pending:
  180 |             ops = (rule_operations or {}).get(id)
  181 |             if ops is None: raise ValueError('RULE_NOT_PREPARED')
  182 |             version = pending['sha256']
  183 |             result = apply_operations(result, ops, id, charge=version not in rule['applied'])
  184 |             rule = result['rules'][id]
  185 |             if rule.get('active'): rule['history'].append(rule['active'])
  186 |             rule['active'], rule['pending'] = pending, None
  187 |             rule['applied'] = sorted(set(rule['applied']+[version]))
  188 |             for job in result.get('jobs',{}).values():
  189 |                 if job.get('rule_id')==id:job['status']='ACTIVE'
  190 |     for _ in range(steps):
  191 |         refresh(result)
  192 |         before = result['life']['tick']
  193 |         old_energy=result['life']['energy']
  194 |         result['life'] = life_step(result['life'], {'kind':action}, PARAMS, result['life']['rng'])
  195 |         result['bio']['Bio_RAM']=min(100,max(0,result['bio']['Bio_RAM']+(result['life']['energy']-old_energy)*100+result['bio']['Swiss_Grey_Weather_Modifier']*.25))
  196 |         if action=='sleep':result['bio']['Sleep_Sync_Index']=min(100,result['bio']['Sleep_Sync_Index']+.5)
  197 |         multiplier = result['bio']['build_multiplier']
  198 |         for n in result['nodes']:
  199 |             if n['status']=='FOCUSED' and action=='work' and result['life']['effective_action']=='work':
  200 |                 n['progress'] = min(100.,round(n['progress']+result['config']['build_per_hour']*.25*multiplier,6))
  201 |             if n['status']=='ACTIVE_CASHFLOW':
  202 |                 # Integer cents allocated by cumulative fractional-day boundaries; no lost hourly rounding.
  203 |                 rate = int(Decimal(daily_economics(n,result['config']['revenue_multiplier'])['contribution_after_reserve'])*100)
  204 |                 delta = math.floor(rate*(before+1)/96)-math.floor(rate*before/96)
  205 |                 n['net_cents'] += delta
  206 |                 result['life']['balance_cents'] += delta; result['life']['net_cents'] += delta
  207 |                 result['tower_net_cents'] += delta
  208 |     return refresh(result)
  209 |
  210 |
  211 | def command(state, name, payload):
  212 |     result = deepcopy(state)
  213 |     if name == 'select_node':
  214 |         keys(payload,['node_id'],['node_id']); node(result,payload['node_id']); result['selected']=payload['node_id']
  215 |     elif name == 'configure_node':
  216 |         keys(payload,['node_id','revenue_day_cents','cost_day_cents','setup_cents','auto_deduct_setup'],['node_id'])
  217 |         n=node(result,payload['node_id'])
  218 |         for key in ('revenue_day_cents','cost_day_cents','setup_cents'):
  219 |             if key in payload:n[key]=number(payload[key],key,0,100000000,True)
  220 |         if 'auto_deduct_setup' in payload:
  221 |             if type(payload['auto_deduct_setup']) is not bool: raise ValueError('INVALID_BOOLEAN')
  222 |             n['auto_deduct_setup']=payload['auto_deduct_setup']
  223 |         if n['status']=='ACTIVE_CASHFLOW':deduct_setup(result,n)
  224 |     elif name == 'node_status':
  225 |         keys(payload,['node_id','status'],['node_id','status'])
  226 |         n = node(result,payload['node_id']); target=payload['status']
  227 |         if target not in {'FOCUSED','SHIPPED','ACTIVE_CASHFLOW'}: raise ValueError('INVALID_STATUS')
  228 |         old = n['status']
  229 |         if target == old: return refresh(result)
  230 |         if old == 'Queued': raise ValueError('QUEUED_NODE_LOCKED')
  231 |         if target=='FOCUSED' or (old in COMPLETE and target != 'ACTIVE_CASHFLOW'):
  232 |             raise ValueError('INVALID_STATUS_TRANSITION')
  233 |         if target=='ACTIVE_CASHFLOW' and old!='SHIPPED': raise ValueError('SHIP_FIRST')
  234 |         if target=='ACTIVE_CASHFLOW':deduct_setup(result,n)
  235 |         n['status']=target
  236 |         if old not in COMPLETE and target in COMPLETE:
  237 |             for candidate in result['nodes']:
  238 |                 if candidate['status']=='Queued':
  239 |                     candidate['status']='FOCUSED'; break
  240 |     elif name == 'activate_quest':
  241 |         keys(payload,[])
  242 |         if result['quest']['start_step'] is None: result['quest']['start_step']=result['life']['tick']
  243 |     elif name == 'verify_milestone':
  244 |         keys(payload,['milestone','evidence'],['milestone','evidence'])
  245 |         milestone=payload['milestone']; text(payload['evidence'],300)
  246 |         if milestone not in result['quest']['milestones']: raise ValueError('UNKNOWN_MILESTONE')
  247 |         # An explicit operator-attested milestone, never inferred from model progress.
  248 |         result['quest']['verified_milestones']=sorted(set(result['quest']['verified_milestones']+[milestone]))
  249 |     elif name == 'update_params':
  250 |         keys(payload,['bio','config'])
  251 |         bio=keys(payload.get('bio',{}),['Bio_RAM','Sleep_Sync_Index','Swiss_Grey_Weather_Modifier','reduced_fog','debuff_hours','debuff_reason','recovery'])
  252 |         for key in ('Bio_RAM','Sleep_Sync_Index','Swiss_Grey_Weather_Modifier'):
  253 |             if key in bio: result['bio'][key]=number(bio[key],key,-.5 if key=='Swiss_Grey_Weather_Modifier' else 0,.5 if key=='Swiss_Grey_Weather_Modifier' else 100)
  254 |         if 'reduced_fog' in bio:
  255 |             if type(bio['reduced_fog']) is not bool: raise ValueError('INVALID_BOOLEAN')
  256 |             result['bio']['reduced_fog']=bio['reduced_fog']
  257 |         if 'recovery' in bio:
  258 |             if bio['recovery'] not in {'Відпочинок','Сон','Чай'}: raise ValueError('AUTOMATIC_RECOVERY_NOT_ALLOWED')
  259 |             result['bio']['recovery']=bio['recovery']
  260 |         if 'debuff_hours' in bio:
  261 |             hours=number(bio['debuff_hours'],'DEBUFF_HOURS',0,48,True)
  262 |             result['bio']['debuff_until_step']=result['life']['tick']+hours*4 if hours else None
  263 |             result['bio']['debuff_reason']=text(bio.get('debuff_reason','Добровільна самооцінка'),100) if hours else None
  264 |         elif ('Bio_RAM' in bio and bio['Bio_RAM']<30) or ('Sleep_Sync_Index' in bio and bio['Sleep_Sync_Index']<40):
  265 |             result['bio']['debuff_until_step']=result['life']['tick']+32
  266 |             result['bio']['debuff_reason']='Сценарний поріг самооцінки: Bio_RAM <30 або Sleep Sync <40; 8 год'
  267 |         cfg=keys(payload.get('config',{}),['trust_min','trust_max','trust_k','gemeinde_deadline','build_per_hour','confidence_assumption','b2b_uplift_assumption'])
  268 |         for key,value in cfg.items():
  269 |             if key=='gemeinde_deadline':
  270 |                 if value is not None and timestamp(value).year not in {2026,2027,2028}: raise ValueError('DEADLINE_SCENARIO_2026_2028')
  271 |                 result['config'][key]=value
  272 |             else: result['config'][key]=number(value,key,0,5 if key=='trust_k' else 100)
  273 |         if result['config']['trust_min']>result['config']['trust_max']: raise ValueError('INVALID_TRUST_BOUNDS')
  274 |     else: raise ValueError('UNKNOWN_COMMAND')
  275 |     return refresh(result)
  276 |
  277 |
  278 | def public_state(state):
  279 |     result=refresh(deepcopy(state))
  280 |     result['rules']={id:{'id':id,'active':r['active']['sha256'] if r.get('active') else None,
  281 |         'pending':r['pending']['sha256'] if r.get('pending') else None,
  282 |         'format':(r.get('pending') or r.get('active') or {}).get('format'),
  283 |         'history':[v['sha256'] for v in r['history']]} for id,r in result['rules'].items()}
  284 |     result['game_theory']=comparison()
  285 |     return result
````

## simulation-core/game_theory_shield.py

Original bytes: 2557; SHA256: `24cfd4d60b2534ac9b7b3c9e2006ca5442c9ecb27bae0bfb498b5666d96ba006`. Original source line numbers follow.

````text
    1 | """Explicit toy strategies, no classification of real people or promised returns."""
    2 | from contracts import keys, number
    3 |
    4 | STRATEGIES = ('Unconditional_Rescuer', 'Exploitative_Narcissist', 'Sovereign_TitForTat')
    5 |
    6 |
    7 | def simulate(left='Unconditional_Rescuer', right='Exploitative_Narcissist', rounds=20,
    8 |              exit_on_breach=False, payoffs=None, energy_cost=1, exploitation_cost=2):
    9 |     if left not in STRATEGIES or right not in STRATEGIES or type(exit_on_breach) is not bool:
   10 |         raise ValueError('UNKNOWN_STRATEGY_OR_EXIT_POLICY')
   11 |     number(rounds, 'ROUNDS', 1, 500, True)
   12 |     number(energy_cost, 'ENERGY_COST', 0, 100)
   13 |     number(exploitation_cost, 'EXPLOITATION_COST', 0, 100)
   14 |     p = dict(T=5, R=3, P=1, S=0) if payoffs is None else dict(keys(payoffs, ['T','R','P','S'], ['T','R','P','S']))
   15 |     for value in p.values():
   16 |         number(value, 'PAYOFF', -100, 100)
   17 |     if not p['T'] > p['R'] > p['P'] > p['S']:
   18 |         raise ValueError('PAYOFF_ORDER_REQUIRES_T_R_P_S')
   19 |     history, total, energy, exploited = [], [0,0], [0,0], [0,0]
   20 |     def action(strategy, previous):
   21 |         if strategy == STRATEGIES[0]: return 'C'
   22 |         if strategy == STRATEGIES[1]: return 'D'
   23 |         return previous or 'C'
   24 |     previous = [None, None]
   25 |     for index in range(rounds):
   26 |         moves = [action(left, previous[1]), action(right, previous[0])]
   27 |         scores = ([p['R'],p['R']] if moves == ['C','C'] else [p['P'],p['P']] if moves == ['D','D']
   28 |                   else [p['S'],p['T']] if moves == ['C','D'] else [p['T'],p['S']])
   29 |         for i in range(2):
   30 |             hit = moves[i] == 'C' and moves[1-i] == 'D'
   31 |             exploited[i] += int(hit)
   32 |             energy[i] += energy_cost + exploitation_cost * hit
   33 |             total[i] += scores[i]
   34 |         history.append(dict(round=index+1, actions=moves, payoff=scores, cumulative=list(total), energy=list(energy)))
   35 |         previous = moves
   36 |         if exit_on_breach and moves[1] == 'D': break
   37 |     return dict(status='SCENARIO_NOT_DIAGNOSIS_OR_GUARANTEE', strategies=[left,right],
   38 |                 requested_rounds=rounds, completed_rounds=len(history), payoffs=p,
   39 |                 energy_cost=energy_cost, exploitation_cost=exploitation_cost,
   40 |                 exit_on_breach=exit_on_breach, cumulative=total, energy=energy,
   41 |                 exploitation_rate=[x/len(history) for x in exploited], history=history)
   42 |
   43 |
   44 | def comparison(rounds=20):
   45 |     return [simulate(left=strategy, rounds=rounds) for strategy in (STRATEGIES[0],STRATEGIES[2])] + [
   46 |         simulate(left=STRATEGIES[2], rounds=rounds, exit_on_breach=True)]
````
