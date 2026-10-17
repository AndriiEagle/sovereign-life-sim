"""Single pure adapter over the unchanged game-forge and Conductor snapshots."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / 'game-forge'))
from sim.core import initial_state as life_initial, load_params, step as life_step
from revenue_lab.core import Quote, evaluate_quote, money
from contracts import identifier, keys, number, text
from game_theory_shield import comparison

PARAMS = load_params()
COMPLETE = {'SHIPPED','ACTIVE_CASHFLOW'}


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None: raise ValueError('TIMEZONE_REQUIRED')
    return parsed.astimezone(timezone.utc)


def initial_state(manifest, seed=42, now='2026-10-18T00:00:00+00:00'):
    timestamp(now)
    projects = manifest['projects']
    ordered = [next(p for p in projects if p['id']==id) for id in ('synera','brand-social-os')]
    ordered += [p for p in projects if p['id'] not in {'synera','brand-social-os'}]
    nodes = []
    for i,p in enumerate(ordered):
        nodes.append(dict(id=p['id'], title=p['title'], manifest_id=p['id'], source_status=p['status'],
                          status='FOCUSED' if i<2 else 'Queued', wave=1 if i<2 else 2 if i<9 else 3,
                          kind='tower' if i<2 else 'mine', progress=0., revenue_day_cents=0,
                          cost_day_cents=0, setup_cents=0, net_cents=0, owner_rule=None))
    life = life_initial(PARAMS, seed=seed)
    state = dict(schema='sovereign.state.v2', revision=0, seed=seed, start_time=now, sim_time=now,
                 life=life, nodes=nodes, selected='synera',
                 bio=dict(Bio_RAM=80, Sleep_Sync_Index=80, Swiss_Grey_Weather_Modifier=0,
                          debuff_reason=None, debuff_until_step=None, reduced_fog=False, recovery='Відпочинок'),
                 config=dict(trust_min=0, trust_max=100, trust_k=.6, gemeinde_deadline=None,
                             build_per_hour=2, confidence_assumption=50, b2b_uplift_assumption=0),
                 quest=dict(start_step=None, verified_milestones=[], milestones=['jwt-two-users','neon-recovery']),
                 rules={}, assets={}, bridge=dict(status='NOT_CONNECTED', providers='NOT_CONNECTED'),
                 economic_remainder=0., tower_net_cents=0)
    return refresh(state)


def node(state, node_id):
    identifier(node_id)
    found = next((n for n in state['nodes'] if n['id']==node_id), None)
    if not found: raise ValueError('UNKNOWN_NODE')
    return found


def refresh(state):
    state['sim_time'] = (timestamp(state['start_time']) + timedelta(minutes=15*state['life']['tick'])).isoformat()
    b = state['bio']
    active = b['debuff_until_step'] is not None and state['life']['tick'] < b['debuff_until_step']
    b['debuff_active'] = active
    b['build_multiplier'] = .6 if active else 1.
    b['fog'] = .12 if b['reduced_fog'] else .48 if active else 0.
    remaining = state['quest']['start_step']
    state['quest']['hours_remaining'] = None if remaining is None else max(0, 48-(state['life']['tick']-remaining)/4)
    cfg = state['config']
    verified = len(state['quest']['verified_milestones'])
    trust = cfg['trust_min']+(cfg['trust_max']-cfg['trust_min'])*(1-math.exp(-cfg['trust_k']*verified))
    deadline = cfg['gemeinde_deadline']
    cash = state['life']['balance_cents']
    burn = PARAMS['money']['daily_cost_cents'] + sum(n['cost_day_cents']-n['revenue_day_cents'] for n in state['nodes'] if n['status']=='ACTIVE_CASHFLOW')
    state['economy'] = dict(status='SYNTHETIC_SCENARIO_NOT_ACTUAL', currency='CHF', cash_cents=cash,
                           Runway_CHF=money(Decimal(cash)/100), runway_days=round(cash/burn,2) if burn>0 else None,
                           actual_cash_chf=None, daily_burn_cents=burn, gilbert_trust_index=round(trust,4),
                           trust_formula='min + (max-min) * (1-exp(-k * verified_milestones))',
                           gemeinde_days_remaining=None if deadline is None else round((timestamp(deadline)-timestamp(state['sim_time'])).total_seconds()/86400,2),
                           gemeinde_status='UNCONFIGURED' if deadline is None else 'SCENARIO_DATE',
                           ROI={n['id']:round(n['net_cents']/n['setup_cents'],4) if n['setup_cents'] else None for n in state['nodes']})
    state['economy']['conductor_nodes']={n['id']:daily_economics(n) for n in state['nodes'] if n['status']=='ACTIVE_CASHFLOW'}
    validate(state)
    return state


def daily_economics(n):
    if not n['revenue_day_cents']:
        return dict(contribution_after_reserve=money(-Decimal(n['cost_day_cents'])/100),status='ZERO_SALES_SCENARIO')
    return evaluate_quote(Quote.from_mapping(dict(currency='CHF',price=money(Decimal(n['revenue_day_cents'])/100),
        fee_rate='0',fee_fixed='0',variable_cost=money(Decimal(n['cost_day_cents'])/100),reserve_rate='0',
        acquisition_hours='0',delivery_hours='1',support_hours='0',hourly_value='0')))


def validate(state):
    if len({n['id'] for n in state['nodes']}) != len(state['nodes']) or len(state['nodes']) > 100:
        raise ValueError('NODE_LIMIT_OR_DUPLICATE')
    if sum(n['status']=='FOCUSED' for n in state['nodes']) > 2:
        raise ValueError('FOCUS_LIMIT')
    for n in state['nodes']:
        identifier(n['id']); text(n['title'])
        number(n['progress'],'PROGRESS',0,100)
        for key in ('revenue_day_cents','cost_day_cents','setup_cents'):
            number(n[key],key,0,100000000,True)
    for key in ('Bio_RAM','Sleep_Sync_Index'):
        number(state['bio'][key],key,0,100)


def apply_operations(state, operations, owner, charge=True):
    if not isinstance(operations,list) or not 1 <= len(operations) <= 8:
        raise ValueError('INVALID_OPERATIONS')
    candidate = deepcopy(state)
    for op in operations:
        if not isinstance(op,dict): raise ValueError('INVALID_OPERATION')
        kind = op.get('op')
        if kind == 'add_node':
            keys(op,['op','id','title','kind','revenue_day_cents','cost_day_cents','setup_cents'],['op','id','title'])
            id = identifier(op['id']); title = text(op['title'])
            existing = next((n for n in candidate['nodes'] if n['id']==id),None)
            if existing and existing['owner_rule'] != owner: raise ValueError('NODE_OWNED_ELSEWHERE')
            if op.get('kind','tower') not in {'tower','mine','agent'}: raise ValueError('INVALID_NODE_KIND')
            fields = dict(title=title, kind=op.get('kind','tower'), **{k:number(op.get(k,0),k,0,100000000,True) for k in ('revenue_day_cents','cost_day_cents','setup_cents')})
            if existing: existing.update(fields)
            else: candidate['nodes'].append(dict(id=id, manifest_id=None, source_status='GENERATED_SCENARIO',
                status='Queued', wave=4, progress=0., net_cents=0, owner_rule=owner, **fields))
        elif kind == 'expense':
            keys(op,['op','amount_cents'],['op','amount_cents'])
            amount = number(op['amount_cents'],'EXPENSE',0,100000000,True)
            if charge:
                if candidate['life']['balance_cents'] < amount: raise ValueError('INSUFFICIENT_SCENARIO_FUNDS')
                candidate['life']['balance_cents'] -= amount; candidate['life']['net_cents'] -= amount
        elif kind == 'set_modifier':
            keys(op,['op','name','value'],['op','name','value'])
            if op['name'] not in {'confidence_assumption','b2b_uplift_assumption'}: raise ValueError('MODIFIER_NOT_ALLOWED')
            candidate['config'][op['name']] = number(op['value'],'MODIFIER',0,100)
        else: raise ValueError('OPERATION_NOT_ALLOWED')
    return refresh(candidate)


def advance(state, steps=4, action='rest', rule_operations=None):
    number(steps,'STEPS',1,672,True)
    if action not in {'rest','sleep','work'}: raise ValueError('UNKNOWN_ACTION')
    result = deepcopy(state)
    for id, rule in result['rules'].items():
        pending = rule.get('pending')
        if pending:
            ops = (rule_operations or {}).get(id)
            if ops is None: raise ValueError('RULE_NOT_PREPARED')
            version = pending['sha256']
            result = apply_operations(result, ops, id, charge=version not in rule['applied'])
            rule = result['rules'][id]
            if rule.get('active'): rule['history'].append(rule['active'])
            rule['active'], rule['pending'] = pending, None
            rule['applied'] = sorted(set(rule['applied']+[version]))
            for job in result.get('jobs',{}).values():
                if job.get('rule_id')==id:job['status']='ACTIVE'
    for _ in range(steps):
        refresh(result)
        before = result['life']['tick']
        old_energy=result['life']['energy']
        result['life'] = life_step(result['life'], {'kind':action}, PARAMS, result['life']['rng'])
        result['bio']['Bio_RAM']=min(100,max(0,result['bio']['Bio_RAM']+(result['life']['energy']-old_energy)*100+result['bio']['Swiss_Grey_Weather_Modifier']*.25))
        if action=='sleep':result['bio']['Sleep_Sync_Index']=min(100,result['bio']['Sleep_Sync_Index']+.5)
        multiplier = result['bio']['build_multiplier']
        for n in result['nodes']:
            if n['status']=='FOCUSED' and action=='work' and result['life']['effective_action']=='work':
                n['progress'] = min(100.,round(n['progress']+result['config']['build_per_hour']*.25*multiplier,6))
            if n['status']=='ACTIVE_CASHFLOW':
                # Integer cents allocated by cumulative fractional-day boundaries; no lost hourly rounding.
                rate = int(Decimal(daily_economics(n)['contribution_after_reserve'])*100)
                delta = math.floor(rate*(before+1)/96)-math.floor(rate*before/96)
                n['net_cents'] += delta
                result['life']['balance_cents'] += delta; result['life']['net_cents'] += delta
                result['tower_net_cents'] += delta
    return refresh(result)


def command(state, name, payload):
    result = deepcopy(state)
    if name == 'select_node':
        keys(payload,['node_id'],['node_id']); node(result,payload['node_id']); result['selected']=payload['node_id']
    elif name == 'configure_node':
        keys(payload,['node_id','revenue_day_cents','cost_day_cents','setup_cents'],['node_id'])
        n=node(result,payload['node_id'])
        for key in ('revenue_day_cents','cost_day_cents','setup_cents'):
            if key in payload:n[key]=number(payload[key],key,0,100000000,True)
    elif name == 'node_status':
        keys(payload,['node_id','status'],['node_id','status'])
        n = node(result,payload['node_id']); target=payload['status']
        if target not in {'FOCUSED','SHIPPED','ACTIVE_CASHFLOW'}: raise ValueError('INVALID_STATUS')
        old = n['status']
        if target == old: return refresh(result)
        if old == 'Queued': raise ValueError('QUEUED_NODE_LOCKED')
        if target=='FOCUSED' or (old in COMPLETE and target != 'ACTIVE_CASHFLOW'):
            raise ValueError('INVALID_STATUS_TRANSITION')
        if target=='ACTIVE_CASHFLOW' and old!='SHIPPED': raise ValueError('SHIP_FIRST')
        n['status']=target
        if old not in COMPLETE and target in COMPLETE:
            for candidate in result['nodes']:
                if candidate['status']=='Queued':
                    candidate['status']='FOCUSED'; break
    elif name == 'activate_quest':
        keys(payload,[])
        if result['quest']['start_step'] is None: result['quest']['start_step']=result['life']['tick']
    elif name == 'verify_milestone':
        keys(payload,['milestone','evidence'],['milestone','evidence'])
        milestone=payload['milestone']; text(payload['evidence'],300)
        if milestone not in result['quest']['milestones']: raise ValueError('UNKNOWN_MILESTONE')
        # An explicit operator-attested milestone, never inferred from model progress.
        result['quest']['verified_milestones']=sorted(set(result['quest']['verified_milestones']+[milestone]))
    elif name == 'update_params':
        keys(payload,['bio','config'])
        bio=keys(payload.get('bio',{}),['Bio_RAM','Sleep_Sync_Index','Swiss_Grey_Weather_Modifier','reduced_fog','debuff_hours','debuff_reason','recovery'])
        for key in ('Bio_RAM','Sleep_Sync_Index','Swiss_Grey_Weather_Modifier'):
            if key in bio: result['bio'][key]=number(bio[key],key,-.5 if key=='Swiss_Grey_Weather_Modifier' else 0,.5 if key=='Swiss_Grey_Weather_Modifier' else 100)
        if 'reduced_fog' in bio:
            if type(bio['reduced_fog']) is not bool: raise ValueError('INVALID_BOOLEAN')
            result['bio']['reduced_fog']=bio['reduced_fog']
        if 'recovery' in bio:
            if bio['recovery'] not in {'Відпочинок','Сон','Чай'}: raise ValueError('AUTOMATIC_RECOVERY_NOT_ALLOWED')
            result['bio']['recovery']=bio['recovery']
        if 'debuff_hours' in bio:
            hours=number(bio['debuff_hours'],'DEBUFF_HOURS',0,48,True)
            result['bio']['debuff_until_step']=result['life']['tick']+hours*4 if hours else None
            result['bio']['debuff_reason']=text(bio.get('debuff_reason','Добровільна самооцінка'),100) if hours else None
        elif ('Bio_RAM' in bio and bio['Bio_RAM']<30) or ('Sleep_Sync_Index' in bio and bio['Sleep_Sync_Index']<40):
            result['bio']['debuff_until_step']=result['life']['tick']+32
            result['bio']['debuff_reason']='Сценарний поріг самооцінки: Bio_RAM <30 або Sleep Sync <40; 8 год'
        cfg=keys(payload.get('config',{}),['trust_min','trust_max','trust_k','gemeinde_deadline','build_per_hour','confidence_assumption','b2b_uplift_assumption'])
        for key,value in cfg.items():
            if key=='gemeinde_deadline':
                if value is not None and timestamp(value).year not in {2026,2027,2028}: raise ValueError('DEADLINE_SCENARIO_2026_2028')
                result['config'][key]=value
            else: result['config'][key]=number(value,key,0,5 if key=='trust_k' else 100)
        if result['config']['trust_min']>result['config']['trust_max']: raise ValueError('INVALID_TRUST_BOUNDS')
    else: raise ValueError('UNKNOWN_COMMAND')
    return refresh(result)


def public_state(state):
    result=deepcopy(state)
    result['rules']={id:{'id':id,'active':r['active']['sha256'] if r.get('active') else None,
        'pending':r['pending']['sha256'] if r.get('pending') else None,
        'format':(r.get('pending') or r.get('active') or {}).get('format'),
        'history':[v['sha256'] for v in r['history']]} for id,r in result['rules'].items()}
    result['game_theory']=comparison()
    return result
