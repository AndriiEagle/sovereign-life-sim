"""Natural-language templates and a validated, versioned plugin boundary."""
from copy import deepcopy
import hashlib
import json
import re

from contracts import canonical, identifier, keys, text
from sandbox import check_source
from unified_tick import apply_operations


def validate_rule(rule):
    keys(rule,['schema','id','format','operations','source','assumptions','origin'],['schema','id','format','assumptions','origin'])
    if rule['schema']!='sovereign.rule.v1' or rule['format'] not in {'json','python'}: raise ValueError('RULE_SCHEMA_UNSUPPORTED')
    identifier(rule['id'])
    if rule['origin'] not in {'offline-template','llm','operator'}: raise ValueError('UNKNOWN_RULE_ORIGIN')
    if not isinstance(rule['assumptions'],list) or len(rule['assumptions'])>8: raise ValueError('INVALID_ASSUMPTIONS')
    for value in rule['assumptions']: text(value,300)
    if rule['format']=='python':
        if 'operations' in rule or 'source' not in rule: raise ValueError('INVALID_PYTHON_RULE')
        check_source(rule['source'])
    elif 'source' in rule or not isinstance(rule.get('operations'),list): raise ValueError('INVALID_JSON_RULE')
    canonical(rule)
    return dict(deepcopy(rule),sha256=hashlib.sha256(canonical(rule).encode()).hexdigest())


def compile_offline(prompt, format='json'):
    prompt=text(prompt,2000)
    if format not in {'json','python'}: raise ValueError('UNKNOWN_RULE_FORMAT')
    lowered=prompt.casefold()
    id='rule-'+hashlib.sha256(prompt.encode()).hexdigest()[:16]
    assumptions=['Synthetic scenario; no actual income, diagnosis, or causal sales prediction.']
    if any(word in lowered for word in ('бот','bot','башт','tower')):
        operations=[dict(op='add_node',id='bot-'+id[5:],title='AI Bot / нова башта',kind='tower')]
        assumptions+=['Revenue defaults to zero until explicit scenario parameters are supplied.']
    elif any(word in lowered for word in ('імплан','имплан','implant','стомат')):
        match=re.search(r'(\d{1,7}(?:[.,]\d{1,2})?)\s*(?:chf|франк)',lowered)
        if not match: raise ValueError('OFFLINE_TEMPLATE_NEEDS_EXPLICIT_CHF_AMOUNT')
        from decimal import Decimal
        amount=int(Decimal(match.group(1).replace(',','.'))*100)
        operations=[dict(op='expense',amount_cents=amount)]
        assumptions+=['Confidence and B2B uplift stay unchanged; compare explicit user-supplied hypotheses in parameters.']
    elif any(word in lowered for word in ('клієн','клиент','client','mirofish','npc')):
        operations=[dict(op='add_node',id='client-'+id[5:],title='Клієнт / сценарний агент',kind='agent')]
        assumptions+=['MiroFish-style local placeholder; upstream MiroFish is NOT_CONNECTED.']
    else:
        raise ValueError('OFFLINE_UNSUPPORTED: supported templates are bot tower, explicit CHF expense, and client agent')
    rule=dict(schema='sovereign.rule.v1',id=id,format=format,assumptions=assumptions,origin='offline-template')
    if format=='python': rule['source']='def evaluate(state, params, seed):\n    return '+repr(operations)+'\n'
    else: rule['operations']=operations
    return validate_rule(rule)


def evaluate(rule, state, sandbox):
    operations=(sandbox.evaluate(rule['source'],dict(tick=state['life']['tick'],cash_cents=state['life']['balance_cents']),state['seed'])
                if rule['format']=='python' else deepcopy(rule['operations']))
    apply_operations(state,operations,rule['id'],charge=rule['sha256'] not in state['rules'].get(rule['id'],{}).get('applied',[]))
    return operations


def stage(state, rule, sandbox):
    # Caller persists the accepted artifact before committing this candidate state.
    raw={k:v for k,v in rule.items() if k!='sha256'}
    verified=validate_rule(raw)
    if verified['sha256']!=rule.get('sha256'): raise ValueError('RULE_HASH_MISMATCH')
    evaluate(verified,state,sandbox)
    result=deepcopy(state)
    entry=result['rules'].setdefault(rule['id'],dict(active=None,pending=None,history=[],applied=[]))
    if entry['pending'] and entry['pending']['sha256']!=rule['sha256']: raise ValueError('RULE_ALREADY_PENDING')
    entry['pending']=verified
    return result
