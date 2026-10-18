# Sovereign source reader: 01-journal, part 1

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## simulation-core/persistence.py

Original bytes: 5671; SHA256: `bceaa99608eb24b6783ca740e44a2f6f7dd8cb7cba6fd740b6329a3a732acab7`. Original source line numbers follow.

````text
    1 | """Durable transactions. The fsynced, hash-chained journal is authoritative."""
    2 | from copy import deepcopy
    3 | import hashlib
    4 | import io
    5 | import json
    6 | import os
    7 | from pathlib import Path
    8 | import threading
    9 | import uuid
   10 |
   11 | from contracts import canonical
   12 |
   13 |
   14 | def digest(value):
   15 |     return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()
   16 |
   17 |
   18 | def atomic_write(path, data):
   19 |     path = Path(path)
   20 |     path.parent.mkdir(parents=True, exist_ok=True)
   21 |     temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
   22 |     try:
   23 |         with temporary.open('xb') as handle:
   24 |             handle.write(data)
   25 |             handle.flush()
   26 |             os.fsync(handle.fileno())
   27 |         os.replace(temporary, path)
   28 |         if os.name != 'nt':
   29 |             descriptor = os.open(path.parent, os.O_RDONLY)
   30 |             try:
   31 |                 os.fsync(descriptor)
   32 |             finally:
   33 |                 os.close(descriptor)
   34 |     finally:
   35 |         temporary.unlink(missing_ok=True)
   36 |
   37 |
   38 | class Store:
   39 |     def __init__(self, directory, initial):
   40 |         self.directory = Path(directory)
   41 |         self.directory.mkdir(parents=True, exist_ok=True)
   42 |         self.lock = threading.RLock()
   43 |         self.changed = threading.Condition(self.lock)
   44 |         self.path = self.directory / 'events.jsonl'
   45 |         self.rows, self.requests = [], {}
   46 |         self.state = deepcopy(initial)
   47 |         self.failed = False
   48 |         # A single local process owns a store, including native MCP adapter clients.
   49 |         self._lease = (self.directory / 'owner.lock').open('a+b')
   50 |         try:
   51 |             if os.name == 'nt':
   52 |                 import msvcrt
   53 |                 self._lease.seek(0)
   54 |                 if not self._lease.read(1):
   55 |                     self._lease.write(b'0'); self._lease.flush()
   56 |                 self._lease.seek(0)
   57 |                 msvcrt.locking(self._lease.fileno(), msvcrt.LK_NBLCK, 1)
   58 |             else:
   59 |                 import fcntl
   60 |                 fcntl.flock(self._lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
   61 |         except OSError:
   62 |             self._lease.close()
   63 |             raise ValueError('STORE_ALREADY_IN_USE') from None
   64 |         try:
   65 |             self._recover()
   66 |             if not self.rows:
   67 |                 self.commit('initial', {}, 'system', 'initial', {}, self.state)
   68 |         except Exception:
   69 |             self.close()
   70 |             raise
   71 |
   72 |     def _recover(self):
   73 |         if not self.path.exists():
   74 |             return
   75 |         data = self.path.read_bytes()
   76 |         good = 0
   77 |         for line in io.BytesIO(data):
   78 |             if not line.endswith(b'\n'):
   79 |                 # Preserve the interrupted tail before truncating it. Never skip a corrupt committed row.
   80 |                 atomic_write(self.directory / ('interrupted-' + uuid.uuid4().hex + '.bin'), line)
   81 |                 with self.path.open('r+b') as handle:
   82 |                     handle.truncate(good); handle.flush(); os.fsync(handle.fileno())
   83 |                 break
   84 |             row = json.loads(line)
   85 |             checksum = row.pop('sha256')
   86 |             if digest(row) != checksum or row['seq'] != len(self.rows) + 1 or row['previous'] != (self.rows[-1]['sha256'] if self.rows else '0' * 64):
   87 |                 raise ValueError('JOURNAL_CORRUPT')
   88 |             row['sha256'] = checksum
   89 |             self.rows.append(row)
   90 |             self.requests[row['request_id']] = row
   91 |             self.state = row['state']
   92 |             good += len(line)
   93 |
   94 |     def get(self):
   95 |         with self.lock:
   96 |             return deepcopy(self.state)
   97 |
   98 |     def duplicate(self, request_id, fingerprint):
   99 |         row = self.requests.get(request_id)
  100 |         if row and row['fingerprint'] != fingerprint:
  101 |             raise ValueError('REQUEST_ID_CONFLICT')
  102 |         return deepcopy(row['result']) if row else None
  103 |
  104 |     def commit(self, kind, payload, source, request_id, result, state, fingerprint=None):
  105 |         with self.lock:
  106 |             if self.failed:
  107 |                 raise OSError('STORE_WRITE_FAILED_RESTART_REQUIRED')
  108 |             state = deepcopy(state)
  109 |             state['revision'] = len(self.rows) + 1
  110 |             row = dict(schema='sovereign.event.v2', seq=state['revision'],
  111 |                        previous=self.rows[-1]['sha256'] if self.rows else '0' * 64,
  112 |                        request_id=request_id, fingerprint=fingerprint or digest([kind, payload]),
  113 |                        sim_time=state['sim_time'], type=kind, source=source, payload=payload,
  114 |                        state=state, result=deepcopy(result))
  115 |             row['sha256'] = digest(row)
  116 |             try:
  117 |                 with self.path.open('ab') as handle:
  118 |                     handle.write((canonical(row) + '\n').encode('utf-8'))
  119 |                     handle.flush(); os.fsync(handle.fileno())
  120 |             except OSError:
  121 |                 self.failed = True
  122 |                 raise
  123 |             self.rows.append(row)
  124 |             self.requests[request_id] = row
  125 |             self.state = state
  126 |             try:
  127 |                 atomic_write(self.directory / 'state.json', canonical(state).encode('utf-8'))
  128 |             except OSError:
  129 |                 # The committed journal is sufficient to recover; a snapshot is only a cache.
  130 |                 pass
  131 |             self.changed.notify_all()
  132 |             return deepcopy(result)
  133 |
  134 |     def events(self, after=0):
  135 |         with self.lock:
  136 |             return [{k:deepcopy(v) for k,v in row.items() if k not in {'state','result','fingerprint','previous'}}
  137 |                     for row in self.rows if row['seq'] > after]
  138 |
  139 |     def close(self):
  140 |         if not self._lease.closed:
  141 |             if os.name == 'nt':
  142 |                 import msvcrt
  143 |                 self._lease.seek(0)
  144 |                 msvcrt.locking(self._lease.fileno(), msvcrt.LK_UNLCK, 1)
  145 |             self._lease.close()
````

## ai-architect/runtime.py

Original bytes: 11559; SHA256: `607237b8e7023bc917cd5ce7790d24578e8e2b12823563ee250ca0ffac3c99ce`. Original source line numbers follow.

````text
    1 | """One durable command dispatcher for HTTP, UI and the MCP adapter."""
    2 | from concurrent.futures import ThreadPoolExecutor
    3 | from copy import deepcopy
    4 | import hashlib
    5 | import json
    6 | from pathlib import Path
    7 | import uuid
    8 |
    9 | from assetforge import AssetForge
   10 | from contracts import canonical, identifier, keys, number, text
   11 | from persistence import Store, atomic_write, digest
   12 | from ruleforge import compile_offline, evaluate, stage, validate_rule
   13 | from sandbox import Sandbox
   14 | from unified_tick import advance, apply_operations, command, initial_state, node, public_state, refresh
   15 | from providers import ProviderGateway
   16 |
   17 |
   18 | class Runtime:
   19 |     def __init__(self, root, directory, generated=None, plugins=None):
   20 |         self.root=Path(root); self.directory=Path(directory)
   21 |         self.assets=AssetForge(generated or self.directory/'generated-assets')
   22 |         self.plugins=Path(plugins or self.directory/'plugins')
   23 |         self.sandbox=Sandbox(self.directory/'sandbox.json')
   24 |         self.providers=ProviderGateway(self.root,self.directory)
   25 |         manifest=json.loads((self.root/'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))
   26 |         self.store=Store(self.directory,initial_state(manifest))
   27 |         self.start_revision=self.store.get()['revision'];self.bridge_confirmed=False
   28 |         self.jobs=ThreadPoolExecutor(max_workers=1,thread_name_prefix='sovereign-forge')
   29 |         with self.store.lock:
   30 |             state=self.store.get()
   31 |             interrupted=False
   32 |             for job in state.get('jobs',{}).values():
   33 |                 if job.get('status') in {'QUEUED','RUNNING'}:
   34 |                     job['status']='INTERRUPTED_NO_RETRY';interrupted=True
   35 |             for asset in state['assets'].values():
   36 |                 if asset.get('status')=='QUEUED':asset['status']='READY';interrupted=True
   37 |             if interrupted:self.store.commit('jobs_interrupted',{},'system','recover-'+uuid.uuid4().hex,{},state)
   38 |             if self.ensure_assets(state):
   39 |                 self.store.commit('assets_ready',{},'system','assets-start-'+uuid.uuid4().hex,{},state)
   40 |
   41 |     def ensure_assets(self,state):
   42 |         changed=False
   43 |         for n in state['nodes']:
   44 |             old=state['assets'].get(n['id'])
   45 |             path=self.assets.directory/(old['key']+'.'+old['format']) if old else None
   46 |             if path and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()!=old['sha256']:
   47 |                 path.unlink()
   48 |             if not old or not path.is_file():
   49 |                 state['assets'][n['id']]=self.assets.fallback(n,old.get('variant',0) if old else 0);changed=True
   50 |         return changed
   51 |
   52 |     def get(self):
   53 |         result=public_state(self.store.get())
   54 |         result['bridge']['status']='LIVE_LOCAL_BRIDGE' if self.bridge_confirmed else 'NOT_CONNECTED'
   55 |         result['capabilities']=dict(python=self.sandbox.report(),provider=self.providers.report(),
   56 |             renderer='EmberIsoKitRenderer with original owned atlas',mcp='Official SDK stdio adapter; provider sessions tracked separately')
   57 |         return result
   58 |
   59 |     def persist_rule(self,rule):
   60 |         atomic_write(self.plugins/(rule['sha256']+'.json'),canonical({k:v for k,v in rule.items() if k!='sha256'}).encode())
   61 |         if rule['format']=='python':atomic_write(self.plugins/(rule['sha256']+'.py'),rule['source'].encode())
   62 |
   63 |     def execute(self,name,payload,request_id,source='ui'):
   64 |         if not isinstance(request_id,str) or not 8<=len(request_id)<=100 or any(not(c.isalnum() or c in '-_') for c in request_id):
   65 |             raise ValueError('INVALID_REQUEST_ID')
   66 |         if not isinstance(payload,dict):raise ValueError('EXPECTED_PAYLOAD_OBJECT')
   67 |         fingerprint=digest([name,payload]);background=None
   68 |         with self.store.lock:
   69 |             previous=self.store.duplicate(request_id,fingerprint)
   70 |             if previous is not None:return previous
   71 |             state=self.store.get();summary={};result=dict(status='PASS',event_id=state['revision']+1,request_id=request_id)
   72 |             if name=='tick':
   73 |                 keys(payload,['steps','hours','days','action'])
   74 |                 dimensions=[k for k in ('steps','hours','days') if k in payload]
   75 |                 if len(dimensions)>1:raise ValueError('AMBIGUOUS_TICK_UNIT')
   76 |                 unit=dimensions[0] if dimensions else 'hours'
   77 |                 amount=number(payload.get(unit,1),unit,1,{'steps':672,'hours':168,'days':7}[unit],True)
   78 |                 steps=amount*{'steps':1,'hours':4,'days':96}[unit];operations={};errors={}
   79 |                 trial=deepcopy(state)
   80 |                 for id,rule in state['rules'].items():
   81 |                     if rule.get('pending'):
   82 |                         try:
   83 |                             ops=evaluate(rule['pending'],trial,self.sandbox)
   84 |                             trial=apply_operations(trial,ops,id,charge=rule['pending']['sha256'] not in rule['applied'])
   85 |                             operations[id]=ops
   86 |                         except (ValueError,OSError) as error:
   87 |                             errors[id]=str(error).split(':')[0];rule['pending']=None
   88 |                 state=advance(state,steps,payload.get('action','rest'),operations)
   89 |                 self.ensure_assets(state);result['rule_errors']=errors
   90 |                 summary=dict(steps=steps,action=payload.get('action','rest'),rule_errors=errors)
   91 |             elif name=='forge_rule':
   92 |                 keys(payload,['prompt','format','rule','use_provider','template_params'])
   93 |                 use_provider=payload.get('use_provider',False)
   94 |                 if type(use_provider) is not bool:raise ValueError('INVALID_BOOLEAN')
   95 |                 if 'rule' in payload:
   96 |                     if 'prompt' in payload or use_provider or 'template_params' in payload:raise ValueError('AMBIGUOUS_RULE_INPUT')
   97 |                     rule=validate_rule(payload['rule'])
   98 |                 elif use_provider:
   99 |                     if 'template_params' in payload:raise ValueError('OFFLINE_TEMPLATE_PARAMS_ONLY')
  100 |                     prompt=text(payload.get('prompt'),2000);self.providers.check('rule')
  101 |                     job_id='job-'+uuid.uuid4().hex
  102 |                     state.setdefault('jobs',{})[job_id]=dict(status='QUEUED',kind='rule')
  103 |                     background=('rule',job_id,dict(prompt=prompt,format=payload.get('format','json')))
  104 |                     rule=None;result.update(status='QUEUED',job_id=job_id);summary=dict(job_id=job_id)
  105 |                 else:rule=compile_offline(payload.get('prompt'),payload.get('format','json'),payload.get('template_params'))
  106 |                 if rule:
  107 |                     state=stage(state,rule,self.sandbox);self.persist_rule(rule)
  108 |                     result.update(status='PENDING_TICK',rule_id=rule['id'],sha256=rule['sha256'])
  109 |                     summary=dict(rule_id=rule['id'],format=rule['format'],sha256=rule['sha256'])
  110 |             elif name=='rollback_rule':
  111 |                 keys(payload,['rule_id'],['rule_id']);id=identifier(payload['rule_id']);rule=state['rules'].get(id)
  112 |                 if not rule:raise ValueError('UNKNOWN_RULE')
  113 |                 if rule['pending']:rule['pending']=None
  114 |                 elif rule['history']:rule['pending']=rule['history'].pop()
  115 |                 else:
  116 |                     rule['active']=None
  117 |                     for n in state['nodes']:
  118 |                         if n['owner_rule']==id:
  119 |                             focused=n['status']=='FOCUSED';n['status']='DISABLED'
  120 |                             if focused:
  121 |                                 queued=next((x for x in state['nodes'] if x['status']=='Queued'),None)
  122 |                                 if queued:queued['status']='FOCUSED'
  123 |                 summary=dict(rule_id=id)
  124 |             elif name=='regenerate_asset':
  125 |                 keys(payload,['node_id','use_provider'],['node_id']);n=node(state,payload['node_id'])
  126 |                 if type(payload.get('use_provider',False)) is not bool:raise ValueError('INVALID_BOOLEAN')
  127 |                 variant=state['assets'].get(n['id'],{}).get('variant',0)+1
  128 |                 state['assets'][n['id']]=self.assets.fallback(n,variant)
  129 |                 result.update(status='READY_OFFLINE',node_id=n['id']);summary=dict(node_id=n['id'],variant=variant)
  130 |                 if payload.get('use_provider'):
  131 |                     self.providers.check('image');job_id='job-'+uuid.uuid4().hex
  132 |                     state['assets'][n['id']]['status']='QUEUED'
  133 |                     state.setdefault('jobs',{})[job_id]=dict(status='QUEUED',kind='image',node_id=n['id'],variant=variant)
  134 |                     background=('image',job_id,dict(node=deepcopy(n),variant=variant));result.update(status='QUEUED',job_id=job_id)
  135 |             elif name=='ack_event':
  136 |                 if source!='mcp':raise ValueError('MCP_CLIENT_REQUIRED')
  137 |                 keys(payload,['event_id'],['event_id']);seq=number(payload['event_id'],'EVENT',self.start_revision+1,state['revision'],True)
  138 |                 if self.store.rows[seq-1]['source']!='mcp':raise ValueError('FOREIGN_EVENT_ACK')
  139 |                 state['bridge']['status']='LIVE_LOCAL_BRIDGE';summary=dict(event_id=seq)
  140 |             elif name=='game_theory':
  141 |                 from game_theory_shield import simulate
  142 |                 keys(payload,['left','right','rounds','exit_on_breach','payoffs','energy_cost','exploitation_cost'])
  143 |                 state['game_theory_custom']=simulate(**payload);summary=dict(rounds=state['game_theory_custom']['completed_rounds'])
  144 |             else:state=command(state,name,payload);summary=deepcopy(payload)
  145 |             refresh(state)
  146 |             self.store.commit(name,summary,source,request_id,result,state,fingerprint)
  147 |             if name=='ack_event':self.bridge_confirmed=True
  148 |         if background:self.jobs.submit(self._background,*background)
  149 |         return result
  150 |
  151 |     def _background(self,kind,job_id,payload):
  152 |         try:
  153 |             data=self.providers.generate(kind,payload['prompt'] if kind=='rule' else self.assets.prompt(payload['node']),payload.get('format','json'))
  154 |             if kind=='rule':
  155 |                 rule=validate_rule(data)
  156 |                 with self.store.lock:
  157 |                     state=stage(self.store.get(),rule,self.sandbox);self.persist_rule(rule)
  158 |                     state['jobs'][job_id]['status']='PENDING_TICK'
  159 |                     state['jobs'][job_id]['rule_id']=rule['id']
  160 |                     self.store.commit('rule_ready',dict(job_id=job_id,rule_id=rule['id']),'system',job_id+'-ready',{},state)
  161 |                 self.execute('tick',{'steps':1,'action':'rest'},job_id+'-activate','system')
  162 |             else:
  163 |                 asset=self.assets.accept_image(payload['node'],data,payload['variant'])
  164 |                 with self.store.lock:
  165 |                     state=self.store.get();id=payload['node']['id']
  166 |                     if state['assets'].get(id,{}).get('variant')==payload['variant']:state['assets'][id]=asset
  167 |                     state['jobs'][job_id]['status']='READY'
  168 |                     self.store.commit('asset_ready',dict(job_id=job_id,node_id=id),'system',job_id+'-ready',{},state)
  169 |         except Exception:
  170 |             with self.store.lock:
  171 |                 state=self.store.get();state.setdefault('jobs',{}).setdefault(job_id,{})['status']='ERROR'
  172 |                 if kind=='image':
  173 |                     asset=state['assets'].get(payload['node']['id'],{})
  174 |                     if asset.get('variant')==payload['variant']:asset.update(status='READY',provider_status='ERROR')
  175 |                 self.store.commit('generation_failed',dict(job_id=job_id,code='GENERATION_FAILED'),'system',job_id+'-failed',{},state)
  176 |
  177 |     def close(self):
  178 |         self.jobs.shutdown(wait=True,cancel_futures=True);self.store.close()
````

## simulation-core/contracts.py

Original bytes: 1295; SHA256: `af423cd7c0a1fd2bfe156f7c88fc6ed64b4bd215b73c6efc18c4292cbcc57134`. Original source line numbers follow.

````text
    1 | """Small shared boundary checks; generated code never runs in this module."""
    2 | import json
    3 | import math
    4 | import re
    5 |
    6 |
    7 | def canonical(value):
    8 |     return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    9 |
   10 |
   11 | def number(value, name, low, high, integer=False):
   12 |     if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
   13 |         raise ValueError('INVALID_' + name)
   14 |     if integer and type(value) is not int:
   15 |         raise ValueError('INTEGER_REQUIRED_' + name)
   16 |     return value
   17 |
   18 |
   19 | def identifier(value):
   20 |     if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', value):
   21 |         raise ValueError('INVALID_ID')
   22 |     return value
   23 |
   24 |
   25 | def text(value, maximum=160):
   26 |     if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
   27 |         raise ValueError('INVALID_TEXT')
   28 |     if re.search(r'(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{15,}|-----BEGIN .*PRIVATE KEY)', value):
   29 |         raise ValueError('SECRET_LIKE_INPUT_REJECTED')
   30 |     return value.strip()
   31 |
   32 |
   33 | def keys(value, allowed, required=()):
   34 |     if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
   35 |         raise ValueError('INVALID_OBJECT_KEYS')
   36 |     return value
````
